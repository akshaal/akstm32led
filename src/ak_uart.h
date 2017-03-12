// GNU GPL blah blah blah (C) Akshaal, 2017 blah blah blah

#ifndef __ak_uart_h
#define __ak_uart_h

#define AK_UART_TX_QUEUE_SIZE 10
#define AK_UART_RX_QUEUE_SIZE 4
#define AK_UART_RX_CHAR_QUEUE_SIZE 100
#define AK_UART_RX_BUF_LEN 80

#define AK_UART_LEFT_KEY "go left"
#define AK_UART_RIGHT_KEY "go right"
#define AK_UART_UP_KEY "go up"
#define AK_UART_DOWN_KEY "go down"

void ak_uart_init();
void ak_uart_send(char const * const str);
char *ak_uart_receive();

#endif
