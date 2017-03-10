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

#define AK_TICK_IN_DAY   (pdMS_TO_TICKS(24 * 60 * 60 * 1000))

void ak_task_delay(const uint32_t millisec);

ak_task_handle ak_task_create(char const *name, const ak_task_f f, const ak_task_priority prio);

ak_task_handle ak_queue_create(int items, int item_size);

void *ak_malloc(size_t xSize);
void ak_free(void *pv);

#endif
