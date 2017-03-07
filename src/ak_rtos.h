#ifndef __ak_rtos_h
#define __ak_rtos_h

#include "FreeRTOS.h"
#include "task.h"

typedef TaskHandle_t ak_task_handle;

typedef void (*ak_task_f) ();

typedef enum {
    ak_main_task_priority = 3
} ak_task_priority;

void ak_task_delay(const uint32_t millisec);

ak_task_handle ak_task_create(char const *name, const ak_task_f f, const ak_task_priority prio);

#endif