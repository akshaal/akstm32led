// GNU GPL blah blah blah (C) Akshaal, 2017 blah blah blah

#include "ak_rtos.h"
#include "ak_led.h"
#include "ak_uart.h"
#include "string.h"
#include "mini-printf.h"

static void ak_main_task(void *argument);
static void help();

#define CMD_TURN_LED_ON "turn light on"
#define CMD_TURN_LED_OFF "turn light off"

void ak_create_main_task() {
    ak_task_create("main", ak_main_task, ak_main_task_priority);
}

__attribute__((noreturn))
static void ak_main_task(void *argument) {
    help();

    for(;;) {
        const char const *cmd = ak_uart_receive();

        if (!strcmp(cmd, "help")) {
            help();
        } else if (!strcmp(cmd, CMD_TURN_LED_ON)) {
            ak_uart_send("LET THERE BE LIGHT!!!!!!!!!\r\n\r\n");
            ak_led_on();
        } else if (!strcmp(cmd, CMD_TURN_LED_OFF)) {
            ak_uart_send("All good things happen in darkness! Now you can start doing good things!!!\r\n\r\n");
            ak_led_off();
        } else if (!strcmp(cmd, AK_UART_DOWN_KEY)) {
            ak_uart_send("You can't go down, you silly!\r\n\r\n");
        } else if (!strcmp(cmd, AK_UART_UP_KEY)) {
            ak_uart_send("There is nothing up there... you can GO up... may be fly?..!\r\n\r\n");
        } else if (!strcmp(cmd, AK_UART_LEFT_KEY) || !strcmp(cmd, AK_UART_RIGHT_KEY)) {
            ak_uart_send("Where is left and where is right?! Can't go there, sorry....\r\n\r\n");
        } else {
            ak_uart_send("You can't do it!! (You just tried to '");
            ak_uart_send(cmd);
            ak_uart_send("'... ahahaha just LOL!!!ONEoneone.. ). You better ask for help!\r\n");

            const size_t len = strlen(cmd);
            if (strlen(cmd) < 5) {
                ak_uart_send("(HEX: ");
                char buf[3];
                for (int i = 0; i < len; i++) {
                    mini_snprintf(buf, 3, "%02X", cmd[i]);
                    ak_uart_send(buf);
                }
                ak_uart_send(")\r\n");
            }

            ak_uart_send("\r\n");
        }

        ak_free(cmd);
    }
}

static void help() {
    ak_uart_send(
        "\r\n"
        "Welcome to the dungeon!\r\n"
        "\r\n"
        "You can:\r\n"
        "  " CMD_TURN_LED_ON " - to turn light on\r\n"
        "  " CMD_TURN_LED_OFF " - to turn light off\r\n"
        "\r\n\r\n"
    );
}
