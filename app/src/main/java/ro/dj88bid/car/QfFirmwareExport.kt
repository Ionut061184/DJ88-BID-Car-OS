package ro.dj88bid.car

import android.app.Activity
import android.app.AlertDialog
import android.app.ProgressDialog
import android.content.Intent
import android.net.Uri
import android.provider.DocumentsContract
import android.system.Os
import android.system.OsConstants
import android.widget.Toast
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.io.IOException
import java.security.MessageDigest
import java.util.Locale
import java.util.concurrent.Executors
import java.util.concurrent.atomic.AtomicBoolean
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream

/**
 * Read-only research export of accessible STATIC OS files, never a flashable image.
 * No root, no shell, no raw partitions, no app data, no network transfer.
 */
class QfFirmwareExport(private val activity: Activity) {
    companion object {
        const val REQUEST = 8218
        private const val PART_BYTES = 160L * 1024 * 1024
        private const val FILE_LIMIT = 40000
    }
    private data class Item(val file: File, val name: String, val size: Long)
    private data class Plan(val parts: List<List<Item>>, val total: Long, val skipped: Int, val notes: List<String>)
    private val executor = Executors.newSingleThreadExecutor()
    private val cancelled = AtomicBoolean(false)
    private var pending: Plan? = null
    private var busy = false
    private var progress: ProgressDialog? = null
    @Volatile private var closed = false

    fun open() {
        if (closed || busy || pending != null) return
        AlertDialog.Builder(activity).setTitle("QF001 · Export sistem pentru analiză")
            .setMessage("Numai citire: APK-uri de sistem, framework, biblioteci și alte fișiere statice accesibile. Nu este firmware complet sau instalabil. Nu include date personale, partiții brute ori MCU. Pot rezulta mai mulți GB. Lucrați numai cu mașina staționată și alimentare stabilă.")
            .setNegativeButton("Anulează", null).setPositiveButton("Inventariază") { _, _ -> scan() }.show()
    }
    private fun progress(title: String) {
        progress = ProgressDialog(activity).apply {
            setTitle(title); setMessage("Se verifică fișierele…")
            setCancelable(false)
            setButton(android.content.DialogInterface.BUTTON_NEGATIVE, "Oprește") { _, _ -> cancelled.set(true) }
            show()
        }
    }
    private fun message(value: String) {
        if (!closed && !activity.isDestroyed) Toast.makeText(activity, value, Toast.LENGTH_LONG).show()
    }
    private fun post(block: () -> Unit) = activity.runOnUiThread {
        if (!closed && !activity.isDestroyed) block()
    }
    private fun finish() { busy = false; progress?.dismiss(); progress = null }
    private fun scan() {
        if (closed || busy) return
        busy = true; cancelled.set(false); progress("Inventar sistem OEM")
        executor.execute {
            try {
                val plan = inventory()
                post {
                    finish()
                    if (cancelled.get()) { message("Inventar oprit."); return@post }
                    if (plan.parts.isEmpty()) { message("Nu există fișiere accesibile pentru export."); return@post }
                    AlertDialog.Builder(activity).setTitle("Export în folderul ales")
                        .setMessage("Fișiere: ${plan.parts.sumOf { it.size }}\nArhive: ${plan.parts.size}\nDimensiune înainte de comprimare: ${plan.total / (1024 * 1024)} MiB\nOmise / inaccesibile: ${plan.skipped}\nAlegeți Download din memoria internă sau un alt folder cu suficient spațiu. Exportul nu este o imagine de restaurare.")
                        .setNegativeButton("Anulează", null)
                        .setPositiveButton("Alege folder") { _, _ ->
                            pending = plan
                            try {
                                activity.startActivityForResult(Intent(Intent.ACTION_OPEN_DOCUMENT_TREE).apply {
                                    addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION)
                                }, REQUEST)
                            } catch (_: Exception) {
                                pending = null; message("Selectorul de foldere nu este disponibil.")
                            }
                        }.show()
                }
            } catch (_: Exception) { post { finish(); message("Inventar incomplet sau oprit.") } }
        }
    }
    private fun permittedName(name: String): Boolean {
        if (name.any { it.code < 32 || it == \'\\\\\' || it == \':\' }) return false
        val n = name.lowercase(Locale.ROOT)
        if (n in setOf("security","keystore","credentials","accounts","keys","private","secrets")) return false
        if (n.contains("password") || n.contains("passwd") || n.contains("shadow") ||
            n.contains("token") || n.contains("secret") || n.contains("private_key") ||
            n.contains("license") || n.contains("credential")) return false
        return listOf(".key",".pem",".p12",".pfx",".jks",".keystore",".der").none { n.endsWith(it) }
    }
    private fun inventory(): Plan {
        val items = ArrayList<Item>()
        val seen = HashSet<String>()
        val notes = ArrayList<String>()
        var skipped = 0
        var visited = 0
        fun omit(name: String) { skipped++; if (notes.size < 200) notes.add(name) }
        fun walk(file: File, name: String, root: File, depth: Int) {
            if (cancelled.get() || closed) throw IOException("cancelled")
            if (++visited > FILE_LIMIT) throw IOException("inventory limit")
            if (depth > 32 || !permittedName(file.name)) { omit(name); return }
            try {
                val stat = Os.lstat(file.path)
                if (OsConstants.S_ISLNK(stat.st_mode)) { omit(name); return }
                val canonical = file.canonicalFile
                if (canonical != root && !canonical.path.startsWith(root.path + "/")) { omit(name); return }
                if (OsConstants.S_ISDIR(stat.st_mode)) {
                    val children = file.listFiles()
                    if (children == null) { omit(name); return }
                    children.sortedBy { it.name }.forEach { walk(it, name + "/" + it.name, root, depth+1) }
                } else if (OsConstants.S_ISREG(stat.st_mode)) {
                    if (!file.canRead() || stat.st_size > PART_BYTES || stat.st_size < 0) { omit(name); return }
                    file.inputStream().use { it.read() } // check actual read access, not only permission bits
                    if (seen.add(canonical.path)) items.add(Item(canonical, name, stat.st_size))
                } else omit(name)
            } catch (e: android.system.ErrnoException) { omit(name) }
              catch (e: SecurityException) { omit(name) }
              catch (e: IOException) { if (cancelled.get() || closed || visited > FILE_LIMIT) throw e; omit(name) }
        }
        // Only named static directories on known OS partitions; never enumerate /data or /dev.
        val dirs = listOf("app","priv-app","framework","lib","lib64","bin","xbin","etc",
            "firmware","overlay","usr","media","apex","build.prop")
        val roots = listOf("/system","/vendor","/product","/odm","/system_ext","/oem")
        for (partition in roots) {
            val base = File(partition).canonicalFile
            if (base.path !in roots && base.path !in roots.filter { it != "/system" }.map { "/system" + it }) { omit(partition); continue }
            if (!base.isDirectory) { omit(partition); continue }
            for (dir in dirs) {
                val f = File(base,dir)
                if (f.exists()) walk(f, partition.removePrefix("/") + "/" + dir, base, 0)
            }
        }
        // Include installed updates of system packages, not user applications or private app files.
        val pm = activity.applicationContext.packageManager
        for (app in pm.getInstalledApplications(0).sortedBy { it.packageName }) {
            if (app.flags and android.content.pm.ApplicationInfo.FLAG_UPDATED_SYSTEM_APP == 0) continue
            if (!app.packageName.matches(Regex("[A-Za-z0-9_.]+"))) continue
            val paths = listOfNotNull(app.sourceDir) + (app.splitSourceDirs?.toList() ?: emptyList())
            for ((index, path) in paths.withIndex()) {
                val file = File(path)
                val root = File("/data/app").canonicalFile
                // Only exact package-manager APK paths are considered; no private data traversal.
                if (!file.name.endsWith(".apk") || !file.canonicalPath.startsWith(root.path + "/")) continue
                walk(file, "updated_system_apks/" + app.packageName + "/" + index + ".apk", root, 0)
            }
        }
        val parts = ArrayList<List<Item>>()
        var part = ArrayList<Item>(); var bytes = 0L
        for (item in items.sortedBy { it.name }) {
            if (part.isNotEmpty() && (bytes + item.size > PART_BYTES || part.size >= 1000)) {
                parts.add(part); part = ArrayList(); bytes = 0
            }
            part.add(item); bytes += item.size
        }
        if (part.isNotEmpty()) parts.add(part)
        return Plan(parts, items.sumOf { it.size }, skipped, notes)
    }
    fun handleResult(request: Int, result: Int, data: Intent?): Boolean {
        if (request != REQUEST) return false
        val plan = pending; pending = null
        val tree = data?.data
        if (result != Activity.RESULT_OK || plan == null || tree == null || tree.scheme != "content" || !DocumentsContract.isTreeUri(tree)) return true
        busy = true; cancelled.set(false); progress("Export sistem în arhive ZIP")
        executor.execute {
            var done = 0
            val resolver = activity.applicationContext.contentResolver
            var current: Uri? = null
            try {
                val parent = DocumentsContract.buildDocumentUriUsingTree(tree, DocumentsContract.getTreeDocumentId(tree))
                val prefix = "QF001-system-" + java.text.SimpleDateFormat("yyyyMMdd-HHmmss",Locale.ROOT).format(java.util.Date())
                for ((index, part) in plan.parts.withIndex()) {
                    if (cancelled.get() || closed) throw IOException("cancelled")
                    post { progress?.setMessage("Arhiva ${index+1} / ${plan.parts.size} · ${done} finalizate") }
                    val filename = prefix + String.format(Locale.ROOT,"-part%03d-of-%03d.zip",index+1,plan.parts.size)
                    val uri = DocumentsContract.createDocument(resolver,parent,"application/zip",filename)
                        ?: throw IOException("document unavailable")
                    current = uri
                    val output = resolver.openOutputStream(uri,"w") ?: throw IOException("destination unavailable")
                    ZipOutputStream(output.buffered()).use { zip ->
                        val manifest = JSONArray()
                        val buffer = ByteArray(128*1024)
                        for (item in part) {
                            if (cancelled.get() || closed) throw IOException("cancelled")
                            val stat = Os.lstat(item.file.path)
                            if (!OsConstants.S_ISREG(stat.st_mode) || stat.st_size != item.size ||
                                item.file.canonicalFile != item.file) throw IOException("file changed")
                            val digest = MessageDigest.getInstance("SHA-256")
                            var copied = 0L
                            zip.putNextEntry(ZipEntry("files/" + item.name))
                            item.file.inputStream().use { input ->
                                while (true) {
                                    if (cancelled.get() || closed) throw IOException("cancelled")
                                    val n = input.read(buffer)
                                    if (n < 0) break
                                    copied += n
                                    if (copied > item.size) throw IOException("file changed")
                                    digest.update(buffer,0,n); zip.write(buffer,0,n)
                                }
                            }
                            if (copied != item.size) throw IOException("file changed")
                            zip.closeEntry()
                            val hash = digest.digest().joinToString("") { "%02x".format(Locale.ROOT,it.toInt() and 255) }
                            manifest.put(JSONObject().put("path",item.name).put("bytes",copied).put("sha256",hash))
                        }
                        val report = JSONObject().put("format","BID_STATIC_SYSTEM_RESEARCH_1")
                            .put("flashable",false).put("completeFirmware",false)
                            .put("build",android.os.Build.DISPLAY).put("fingerprint",android.os.Build.FINGERPRINT)
                            .put("part",index+1).put("partCount",plan.parts.size)
                            .put("omittedCount",plan.skipped).put("omittedExamples",JSONArray(plan.notes))
                            .put("files",manifest)
                        zip.putNextEntry(ZipEntry("manifest.json"))
                        zip.write(report.toString(2).toByteArray(Charsets.UTF_8)); zip.closeEntry()
                    }
                    current = null; done++
                }
                post { finish(); message("Export salvat: $done arhive ZIP. Trimiteți-le pentru analiză, nu le instalați.") }
            } catch (_: Exception) {
                current?.let { try { DocumentsContract.deleteDocument(resolver,it) } catch (_: Exception) {} }
                post { finish(); message("Export oprit/incomplet: $done arhive finalizate. Nu utilizați ultima arhivă dacă a rămas incompletă.") }
            }
        }
        return true
    }
    fun close() {
        closed = true; cancelled.set(true); executor.shutdownNow()
        pending = null; progress?.dismiss(); progress = null
    }
}
