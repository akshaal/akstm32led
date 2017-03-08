# GNU GPL blah blah blah (C) Akshaal, 2017 blah blah blah

TARGET              = akstm32le
PREFIX              = arm-none-eabi
MCPU                = cortex-m3
CUBEFILE_REL        = misc/stm32cubef1.zip # File downloaded from st.com site
STM32_TARGET_DEF    = STM32F103xB
FREE_RTOS_PORT      = ARM_CM3
FREE_RTOS_HEAP      = heap_4
STARTUP_S           = startup_stm32f103xb.s

SRCS_MY         = ak_main_task.c ak_rtos.c ak_led.c ak_led_fatal_ind.c
SRCS            = main.c stm32f1xx_it.c stm32f1xx_hal_timebase_TIM.c ${SRCS_MY}
SRCS_3RD        = system_stm32f1xx.c stm32f1xx_hal.c stm32f1xx_hal_rcc.c # HAL
SRCS_3RD       += stm32f1xx_hal_cortex.c stm32f1xx_hal_gpio.c stm32f1xx_hal_tim.c stm32f1xx_hal_tim_ex.c # HAL
SRCS_3RD       += stm32f1xx_hal_msp.c # HAL
SRCS_3RD       += stm32f1xx_hal_uart.c # HAL UART
SRCS_3RD       += cmsis_os.c tasks.c queue.c list.c timers.c # FreeRTOS
SRCS_3RD       += croutine.c event_groups.c port.c ${FREE_RTOS_HEAP}.c # FreeRTOS

CMSIS_BASE      = Drivers/CMSIS/Device/ST/STM32F1xx
CMSIS_SRCS      = Templates/system_stm32f1xx.c Templates/gcc/${STARTUP_S}

HAL_BASE        = Drivers/STM32F1xx_HAL_Driver

LDFILE          = src/STM32F103XB_FLASH_64k.ld

# Compiler flags
CFLAGS  = -Wall # All warnings
CFLAGS += -save-temps=obj # Save temporary files (assembler etc) based on obj file location
CFLAGS += -g # Enable debug symbols in elf file
CFLAGS += -std=gnu11 # Use GNU C 2011
#CFLAGS += -O4 # Optimize for speed
CFLAGS += -Os # Optimize for size
#CFLAGS += -O0 # Optimize for nothing
#CFLAGS += -funroll-loops # Unroll loops
CFLAGS += -mcpu=${MCPU}
CFLAGS += -mthumb # Generate either Thumb-1 (16bit) or Thumb-2 (32bit) instructions
CFLAGS += -fno-strict-aliasing # Makes more optimization possible
CFLAGS += -ffreestanding # Assert that compilation targets a freestanding environment.
CFLAGS += -flto # Enable link time optimization
CFLAGS += -fwhole-program # Enable whole program optimization
CFLAGS += --specs=nosys.specs # no complain about _exit and stuff
CFLAGS += -Isrc-3rd # Include 3rd party sources
CFLAGS += -Isrc # ... sources
CFLAGS += -D${STM32_TARGET_DEF} # Define target that's needed by stm32f1xx.h

# Linked flags
LDFLAGS  = -Wl,--gc-sections # Remove unused sections (e.g. remove unused data and functions)
LDFLAGS += -Wl,--relax # Perform optimizations in linker
LDFLAGS += -Wl,-Map=tmp/$(TARGET).map # Write map file
LDFLAGS += -T${LDFILE} # Link script
LDFLAGS += -lc # Use standard C file

# Applications
AR          = $(PREFIX)-ar
CC          = $(PREFIX)-gcc
GDB         = $(PREFIX)-gdbd
OBJCOPY     = $(PREFIX)-objcopy
OBJDUMP     = $(PREFIX)-objdump
SIZE        = $(PREFIX)-size

SRCS_3RD_WP = $(addprefix src-3rd/,${SRCS_3RD})

# Generate list of object files (.o) and dependency files (.d)
# Dependency files are the one that are generated by GCC by using MMD MF options
OBJS_3RD    = $(addprefix tmp/,$(SRCS_3RD:.c=.o))
OBJS        = $(addprefix tmp/,$(SRCS:.c=.o)) ${OBJS_3RD}
DEPS        = $(addprefix tmp/,$(SRCS:.c=.d)) $(addprefix tmp/,$(SRCS_3RD:.c=.d))

###################################################################################################

# Some useful info about makefile syntax:
#    targets : normal-prerequisites | order-only-prerequisites

###################################################################################################

# First rule is the default one
all: bin/$(TARGET).bin | dirs

${OBJS_3RD}: ${SRCS_3RD_WP} | dirs

${SRCS_3RD_WP}: dirs

# Include dependncy files (generated by GCC)
-include $(DEPS)

bin/$(TARGET).bin: $(OBJS) | dirs
	$(CC) $(CFLAGS) $(LDFLAGS) src-3rd/${STARTUP_S} $^ -o tmp/$(TARGET).elf
	$(OBJDUMP) -St tmp/$(TARGET).elf >tmp/$(TARGET).lst
	$(SIZE) tmp/$(TARGET).elf
	$(OBJCOPY) -O binary tmp/$(TARGET).elf bin/$(TARGET).bin

tmp/%.o : src/%.c | dirs
	$(CC) $(CFLAGS) -c -o $@ $< -MMD -MF tmp/$(*F).d

tmp/%.o : src-3rd/%.c | dirs
	$(CC) $(CFLAGS) -c -o $@ $< -MMD -MF tmp/$(*F).d

.PHONY: all clean dirs

dirs: cube src-3rd

cube: | ${CUBEFILE_REL}
	cd tmp && unzip ../${CUBEFILE_REL}
	mv tmp/STM32Cube* cube
	chmod 755 cube

src-3rd: cube
	mkdir src-3rd src-3rd/Legacy
	cp cube/${CMSIS_BASE}/Include/*.h src-3rd/
	cp $(addprefix cube/${CMSIS_BASE}/Source/,${CMSIS_SRCS}) src-3rd/
	cp cube/${HAL_BASE}/Inc/*.h src-3rd/
	cp cube/${HAL_BASE}/Src/*.c src-3rd/
	cp cube/${HAL_BASE}/Inc/Legacy/*.h src-3rd/Legacy/
	cp cube/Drivers/CMSIS/Include/* src-3rd/
	cp cube/Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS/* src-3rd/
	cp cube/Middlewares/Third_Party/FreeRTOS/Source/include/* src-3rd/
	cp cube//Middlewares/Third_Party/FreeRTOS/Source/portable/GCC/${FREE_RTOS_PORT}/* src-3rd/
	cp cube//Middlewares/Third_Party/FreeRTOS/Source/portable/MemMang/${FREE_RTOS_HEAP}.c src-3rd/
	cp cube//Middlewares/Third_Party/FreeRTOS/Source/*.c src-3rd/
	dos2unix src-3rd/task.h # We are going to patch it...
	patch -p1 < src-3rd.patch

clean:
	rm -f tmp/*.o tmp/*.map tmp/*.elf tmp/*.lst bin/*.bin tmp/*.d tmp/*.map tmp/*.i tmp/*.s tmp/*.res tmp/*.zip
	rm -rf tmp/STM32*
	rm -rf cube src-3rd
