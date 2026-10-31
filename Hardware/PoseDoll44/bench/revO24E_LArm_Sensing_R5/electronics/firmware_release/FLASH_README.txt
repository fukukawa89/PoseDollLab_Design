R5 firmware for O22 carrier + XIAO ESP32S3 with R5 WD adapter only.
No hardware was flashed in preparation of this release.
Disconnect sensor power for initial flash; verify wiring against WIRING.html before power-up.
Install esptool v5.3.1, then run in THIS directory with the actual COM port:
python -m esptool --chip esp32s3 --port COM_ACTUAL -b 460800 --before default-reset --after hard-reset write-flash --flash-mode dio --flash-size 8MB --flash-freq 80m 0x0 bootloader.bin 0x8000 partition-table.bin 0x10000 PoseDoll_R5_7axis_USB.bin
Do not use a guessed port. This command overwrites firmware on the selected controller. Back up any firmware/settings you need first.
The ELF project name remains posedoll_o21_usb_raw46 for compatibility with the inherited build script; the protocol and source are R5AR.
Sensor EN remains high. WD CS is GPIO3, NOT GPIO1. A01 pin5 is SDI. See exact six-wire adapter table.
