To use build-test-build-test-build-test:
1. Start connect-to-device-via-stlink
2. Start open-gdb-via-stlink and peridically do 'restart' command there

In order to see output from stm32 (via serial interface on GPIOA) run 'open-stlink-console'

To flash production firmware start 'open-stlink-console' and type 'make' and then 'write'.
