package ro.dj88bid.car

import android.app.Activity
import android.app.AlertDialog
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.util.AtomicFile
import android.widget.ImageView
import android.widget.Toast
import java.io.File

/** Private BID artwork library. No OEM model replacement or camera control. */
class BidCarArtwork(private val activity: Activity) {
    private val slots = arrayOf("Vedere de sus", "Față", "Spate", "Lateral stânga",
        "Lateral dreapta", "Perspectivă 3/4")
    private val baseCode = 540
    private val maxBytes = 16L * 1024 * 1024
    private var importing = false
    private fun file(slot: Int) = File(activity.filesDir, "bid_car_art_${slot}.img")
    private fun preview(file: File): Bitmap? {
        val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        BitmapFactory.decodeFile(file.path, bounds)
        val width = bounds.outWidth
        val height = bounds.outHeight
        if (width !in 1..8192 || height !in 1..8192 ||
            width.toLong() * height.toLong() > 40000000L) return null
        if (bounds.outMimeType !in setOf("image/png", "image/jpeg", "image/webp")) return null
        var sample = 1
        while (maxOf(width, height) / sample > 1024) sample *= 2
        return BitmapFactory.decodeFile(file.path, BitmapFactory.Options().apply { inSampleSize = sample })
    }
    fun show() {
        if (activity.isFinishing || activity.isDestroyed) return
        val labels = slots.mapIndexed { i, name -> name + if (file(i).isFile) " · importată" else " · necompletată" }.toTypedArray()
        AlertDialog.Builder(activity).setTitle("BID · Atelier imagini 360°")
            .setItems(labels) { _, i -> slotMenu(i) }
            .setNegativeButton("Închide", null).show()
    }
    private fun slotMenu(slot: Int) {
        AlertDialog.Builder(activity).setTitle(slots[slot])
            .setItems(arrayOf("Importă / înlocuiește imaginea", "Previzualizează", "Șterge imaginea BID")) { _, choice ->
                when (choice) {
                    0 -> pick(slot)
                    1 -> {
                        val bitmap = try { preview(file(slot)) } catch (_: Exception) { null }
                        if (bitmap == null) toast("Nu există o imagine validă.")
                        else {
                            val view = ImageView(activity).apply {
                                setImageBitmap(bitmap)
                                adjustViewBounds = true
                                scaleType = ImageView.ScaleType.FIT_CENTER
                            }
                            val dialog = AlertDialog.Builder(activity).setTitle(slots[slot])
                                .setView(view).setPositiveButton("Închide", null).create()
                            dialog.setOnDismissListener { view.setImageDrawable(null); bitmap.recycle() }
                            dialog.show()
                        }
                    }
                    2 -> AlertDialog.Builder(activity).setTitle("Ștergi imaginea BID?")
                        .setMessage("Nu se modifică imaginile originale OEM.")
                        .setNegativeButton("Anulează", null)
                        .setPositiveButton("Șterge") { _, _ -> AtomicFile(file(slot)).delete(); show() }.show()
                }
            }.setNegativeButton("Înapoi") { _, _ -> show() }.show()
    }
    private fun pick(slot: Int) {
        if (importing) { toast("Un import este deja în curs."); return }
        try {
            activity.startActivityForResult(Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
                addCategory(Intent.CATEGORY_OPENABLE)
                type = "image/*"
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            }, baseCode + slot)
        } catch (_: Exception) { toast("Selectorul de fișiere nu este disponibil.") }
    }
    fun handleResult(code: Int, result: Int, data: Intent?) {
        val slot = code - baseCode
        if (slot !in slots.indices || result != Activity.RESULT_OK || importing) return
        val uri = data?.data ?: return
        if (uri.scheme != "content") { toast("Selectează un document valid."); return }
        importing = true
        Thread {
            var temp: File? = null
            var success = false
            try {
                val staging = File.createTempFile("bid_art_", ".tmp", activity.cacheDir)
                temp = staging
                activity.contentResolver.openInputStream(uri)?.use { input ->
                    staging.outputStream().use { out ->
                        val buf = ByteArray(65536)
                        var total = 0L
                        while (true) {
                            val n = input.read(buf)
                            if (n < 0) break
                            total += n
                            require(total <= maxBytes)
                            out.write(buf, 0, n)
                        }
                    }
                } ?: error("No stream")
                val bitmap = preview(staging) ?: error("Invalid image")
                bitmap.recycle()
                val target = AtomicFile(file(slot))
                val out = target.startWrite()
                try {
                    staging.inputStream().use { it.copyTo(out) }
                    target.finishWrite(out)
                } catch (e: Exception) { target.failWrite(out); throw e }
                success = true
            } catch (_: Exception) {
                // Invalid or oversized file never replaces existing artwork.
            } finally { temp?.delete() }
            activity.runOnUiThread {
                importing = false
                if (!activity.isFinishing && !activity.isDestroyed) {
                    toast(if (success) "Imagine importată fără modificarea fișierului." else
                        "Import respins. PNG/JPEG/WebP, max. 16 MB și 8192 pixeli/latură.")
                    show()
                }
            }
        }.start()
    }
    private fun toast(text: String) = Toast.makeText(activity, text, Toast.LENGTH_LONG).show()
}
