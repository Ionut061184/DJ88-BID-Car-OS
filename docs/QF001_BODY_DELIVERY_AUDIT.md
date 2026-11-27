# QF001 body data delivery audit

Base: Update 5 APK commit 8e1e476. User reports speed and fuel unavailable on device; OEM body page displays actual values. Installed CANBUS V1.11-260615.1900; reference extracted OEM APK is older V1.8-250611.1730. Do not extrapolate compatibility.

## Evidence from reference APK DEX
- DataShareManager.getInstance reads KeyAllPackages, appends own package if missing, writes it using GlobalSettingUtil.setAllRequestDataPackages, then registers DATA_SHARE receiver.
- DataShareManager.addCarBodyStateCallBack calls GlobalSettingUtil.setIsShareCarbodyState when sharing is not enabled. GlobalSettingUtil uses package name + KeyShareCarbodyState. GlobalSetting writes through Settings.Global.putInt / putString. BID manifest does not declare WRITE_SECURE_SETTINGS; no privileged writes or registry changes are performed by this candidate.
- VehicleSender.showCarbodyState / 2 / 3 call DataPackageUtil.getCarInfoByte and broadcast com.qf.vehicle.action.DATA_SHARE with extra_DATA_SHARE. The 79-byte serializer includes speed, RPM, fuel, odometer and handbrake/washer bits but no mBatteryVoltage reference. CarBodyFragment.initCarbodyState displays mBatteryVoltage. Existing header sys.qf.update_battery_power is not that source. Do not add a fixed voltage offset.

## Candidate changes
Read-only diagnostic of installed CANBUS version, package registry, delivery state and privilege. Seven compact rows in existing bottom-side spaces, no MASTER image or original touch zone changes; installed OEM resource lookup with allowlisted names. Unknown/expired data are withdrawn; warning labels and colors remain locked behind verified mapping. The current native probe deliberately reports verified=false. No unsupported normal/low warning state is asserted. No firmware or MCU commands.

## Checks
JavaScript parsed and executed in a simulated DOM with missing, fresh candidate, verified fixture and stale inputs. Seven rows, no duplicate fuel, correct unavailable states; fixture warning states red/yellow. This is not a device or Gradle test. Need actual V1.11 data and registration permission path, OEM warning mapping, comparison of both voltage sources and a build tested on stationary vehicle. Never use BID as a certified speedometer.
