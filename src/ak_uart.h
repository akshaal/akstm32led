// GNU GPL blah blah blah (C) Akshaal, 2017 blah blah blah

#ifndef __ak_uart_h
#define __ak_uart_h

#define AK_UART_TX_QUEUE_SIZE 50
#define AK_UART_RX_QUEUE_SIZE 10
#define AK_UART_RX_CHAR_QUEUE_SIZE 100
#define AK_UART_RX_BUF_LEN 80

void ak_uart_init();
void ak_uart_send(char *str);

#endif
