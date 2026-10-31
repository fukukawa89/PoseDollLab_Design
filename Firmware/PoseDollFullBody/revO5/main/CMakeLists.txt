idf_component_register(SRCS "main.c" "../static_gateway.c" INCLUDE_DIRS ".." "../../main" REQUIRES esp_driver_spi esp_driver_gpio esp_driver_usb_serial_jtag esp_driver_twai esp_timer esp_hw_support)
