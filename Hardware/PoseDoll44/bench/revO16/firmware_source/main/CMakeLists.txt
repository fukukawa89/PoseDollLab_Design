idf_component_register(SRCS "main.c" "../raw46.c" INCLUDE_DIRS ".." REQUIRES esp_wifi esp_event nvs_flash esp_driver_spi esp_driver_gpio esp_driver_usb_serial_jtag esp_timer esp_hw_support)
