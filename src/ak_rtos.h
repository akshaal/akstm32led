// GNU GPL blah blah blah (C) Akshaal, 2017 blah blah blah

#ifndef __ak_rtos_h
#define __ak_rtos_h

#include "FreeRTOS.h"
#include "task.h"
#include "queue.h"

typedef TaskHandle_t ak_task_handle;
typedef QueueHandle_t ak_queue_handle;

typedef void (*ak_task_f) ();

typedef enum {
    ak_uart_tx_task_priority = 1,
    ak_uart_rx_task_priority = 1,
    ak_main_task_priority = 3
} ak_task_priority;

#define AK_TICKS_IN_DAY   (pdMS_TO_TICKS(24 * 60 * 60 * 1000))

void ak_task_delay(uint32_t const millisec);

ak_task_handle ak_task_create(char const * const name, ak_task_f const f, ak_task_priority const prio);

ak_task_handle ak_queue_create(int const items, size_t const item_size);

void *ak_malloc(size_t const size);
void ak_free(void const * const pv);
char *ak_strdup(char const * const s);
char *ak_strndup(char const * const s, size_t const size);

#ifdef AK_DBG
#include "ak_uart.h"

#define ak_debug(str)  ak_uart_send(str)
#else
#define ak_debug(str)
#endif

#endif
