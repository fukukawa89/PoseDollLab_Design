from common import *

def run():
    src=OUT/'verification/firmware_build/USB';dst=OUT/'electronics/firmware_release';dst.mkdir(exist_ok=True)
    items=[]
    for old,new,offset in [('bootloader/bootloader.bin','bootloader.bin','0x0'),('partition_table/partition-table.bin','partition-table.bin','0x8000'),('posedoll_o21_usb_raw46.bin','PoseDoll_R5_7axis_USB.bin','0x10000')]:
        shutil.copyfile(src/old,dst/new);items.append(dict(file=new,offset=offset,sha256=sha(dst/new),bytes=(dst/new).stat().st_size))
    files={p.relative_to(OUT/'electronics/firmware_source').as_posix():sha(p) for p in (OUT/'electronics/firmware_source').rglob('*') if p.is_file()}
    put(dst/'manifest.json',dict(status='COMPILED_NOT_FLASHED',chip='esp32s3',idf='v6.1',build_date='2026-10-30',protocol='R5AR v1 / 280 bytes / 6 MT + 1 TMAG',files=items,source_sha256=files,hardware_tested=False,flash=dict(mode='dio',size='8MB',frequency='80m')))
    (dst/'FLASH_README.txt').write_text('R5 firmware for O22 carrier + XIAO ESP32S3 with R5 WD adapter only.\nNo hardware was flashed in preparation of this release.\nDisconnect sensor power for initial flash; verify wiring against WIRING.html before power-up.\nInstall esptool v5.3.1, then run in THIS directory with the actual COM port:\npython -m esptool --chip esp32s3 --port COM_ACTUAL -b 460800 --before default-reset --after hard-reset write-flash --flash-mode dio --flash-size 8MB --flash-freq 80m 0x0 bootloader.bin 0x8000 partition-table.bin 0x10000 PoseDoll_R5_7axis_USB.bin\nDo not use a guessed port. This command overwrites firmware on the selected controller. Back up any firmware/settings you need first.\nThe ELF project name remains posedoll_o21_usb_raw46 for compatibility with the inherited build script; the protocol and source are R5AR.\nSensor EN remains high. WD CS is GPIO3, NOT GPIO1. A01 pin5 is SDI. See exact six-wire adapter table.\n',encoding='utf8')
    print('FIRMWARE release',[(r['file'],r['bytes']) for r in items],flush=True)

if __name__=='__main__':run()

