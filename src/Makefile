# MinGW release builds with native and portable x86-64-v3 profiles.
.DEFAULT_GOAL := native

CXX   ?= g++
STRIP ?= strip

PROFILE ?= native
BIN     ?= ../nullstar_mingw_native_nonpgo.exe

SUPPORTED_PROFILES := native v3
ifeq ($(filter $(PROFILE),$(SUPPORTED_PROFILES)),)
$(error Unsupported PROFILE '$(PROFILE)'; choose native or v3)
endif

BUILD_ROOT ?= ../build/mingw
BUILD_DIR  := $(BUILD_ROOT)/$(PROFILE)

WARN_FLAGS    := -Wall -Wextra -Wpedantic
COMMON_FLAGS  := -std=c++23 -O3 -DNDEBUG -pipe -flto=auto -fno-rtti \
                 -fipa-pta -fno-semantic-interposition
NATIVE_FLAGS  := -march=native -mtune=native
V3_FLAGS      := -march=x86-64-v3 -mtune=generic
PROFILE_FLAGS := $(if $(filter native,$(PROFILE)),$(NATIVE_FLAGS),$(V3_FLAGS))

ifeq ($(OS),Windows_NT)
  remove_dir = if exist "$(subst /,\,$1)" rmdir /s /q "$(subst /,\,$1)"
  remove_file = if exist "$(subst /,\,$1)" del /q "$(subst /,\,$1)"
else
  remove_dir = rm -rf "$1"
  remove_file = rm -f "$1"
endif

CXXFLAGS += $(WARN_FLAGS) $(COMMON_FLAGS) $(PROFILE_FLAGS) -MMD -MP
LDFLAGS  += -static -flto=auto -fipa-pta -fno-semantic-interposition

# Generation and use builds share an object path because GCC keys profile
# files to it. Public PGO targets always discard stale profiles first.
PGO ?= none
PGO_DATA_ROOT ?= ../build/pgo-data
PGO_DATA_DIR := $(abspath $(PGO_DATA_ROOT)/$(PROFILE))
ifeq ($(PGO),generate)
  CXXFLAGS += -fprofile-generate=$(PGO_DATA_DIR)
  LDFLAGS  += -fprofile-generate=$(PGO_DATA_DIR)
else ifeq ($(PGO),use)
  CXXFLAGS += -fprofile-use=$(PGO_DATA_DIR) -fprofile-correction \
              -fprofile-partial-training -Wno-missing-profile
  LDFLAGS  += -fprofile-use=$(PGO_DATA_DIR) -fprofile-correction \
              -fprofile-partial-training
else ifneq ($(PGO),none)
  $(error Unsupported PGO mode '$(PGO)'; choose none, generate, or use)
endif

SRC := $(wildcard *.cpp)
OBJ := $(patsubst %.cpp,$(BUILD_DIR)/%.o,$(SRC))
DEP := $(OBJ:.o=.d)

.PHONY: all build release native avx2 v3 pgo pgo-native pgo-avx2 pgo-v3 \
        info clean distclean

all build: $(BIN)

release: $(BIN)
	$(STRIP) $(BIN)

native:
	$(MAKE) --no-print-directory PROFILE=native \
		BIN=../nullstar_mingw_native_nonpgo.exe release

avx2:
	$(MAKE) --no-print-directory PROFILE=v3 \
		BIN=../nullstar_mingw_avx2_nonpgo.exe release

# Backward-compatible compiler-profile alias.
v3: avx2

PGO_DEPTH ?= 13
PGO_BUILD_ROOT ?= ../build/mingw-pgo

pgo: pgo-native pgo-avx2

pgo-native:
	@$(call remove_dir,$(PGO_DATA_ROOT)/native)
	@$(call remove_dir,$(PGO_BUILD_ROOT)/native)
	$(MAKE) --no-print-directory -B PROFILE=native PGO=generate \
		BUILD_ROOT=$(PGO_BUILD_ROOT) \
		BIN=../build/nullstar_mingw_native_pgo_train.exe build
ifeq ($(OS),Windows_NT)
	@(echo bench $(PGO_DEPTH)& echo quit) | \
		..\build\nullstar_mingw_native_pgo_train.exe >NUL
else
	printf 'bench $(PGO_DEPTH)\nquit\n' | \
		../build/nullstar_mingw_native_pgo_train.exe >/dev/null
endif
	$(MAKE) --no-print-directory -B PROFILE=native PGO=use \
		BUILD_ROOT=$(PGO_BUILD_ROOT) BIN=../nullstar_mingw_native_pgo.exe release

pgo-avx2:
	@$(call remove_dir,$(PGO_DATA_ROOT)/v3)
	@$(call remove_dir,$(PGO_BUILD_ROOT)/v3)
	$(MAKE) --no-print-directory -B PROFILE=v3 PGO=generate \
		BUILD_ROOT=$(PGO_BUILD_ROOT) \
		BIN=../build/nullstar_mingw_avx2_pgo_train.exe build
ifeq ($(OS),Windows_NT)
	@(echo bench $(PGO_DEPTH)& echo quit) | \
		..\build\nullstar_mingw_avx2_pgo_train.exe >NUL
else
	printf 'bench $(PGO_DEPTH)\nquit\n' | \
		../build/nullstar_mingw_avx2_pgo_train.exe >/dev/null
endif
	$(MAKE) --no-print-directory -B PROFILE=v3 PGO=use \
		BUILD_ROOT=$(PGO_BUILD_ROOT) BIN=../nullstar_mingw_avx2_pgo.exe release

# Backward-compatible compiler-profile alias.
pgo-v3: pgo-avx2

$(BIN): $(OBJ)
	$(CXX) $(OBJ) $(LDFLAGS) $(LDLIBS) -o $@

$(BUILD_DIR)/%.o: %.cpp | $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) -c $< -o $@

$(BUILD_DIR):
ifeq ($(OS),Windows_NT)
	@if not exist "$(subst /,\,$@)" mkdir "$(subst /,\,$@)"
else
	@mkdir -p "$@"
endif

info:
	@echo PROFILE=$(PROFILE)
	@echo BIN=$(BIN)
	@echo BUILD_DIR=$(BUILD_DIR)
	@echo CXX=$(CXX)
	@echo CXXFLAGS=$(CXXFLAGS)
	@echo LDFLAGS=$(LDFLAGS)

clean:
	@$(call remove_dir,$(BUILD_DIR))
	@$(call remove_file,$(BIN))

distclean:
	@$(call remove_dir,$(BUILD_ROOT))
	@$(call remove_dir,$(PGO_BUILD_ROOT))
	@$(call remove_dir,$(PGO_DATA_ROOT))
	@$(call remove_file,../build/nullstar_mingw_native_pgo_train.exe)
	@$(call remove_file,../build/nullstar_mingw_avx2_pgo_train.exe)
	@$(call remove_file,../nullstar_mingw_native_nonpgo.exe)
	@$(call remove_file,../nullstar_mingw_native_pgo.exe)
	@$(call remove_file,../nullstar_mingw_avx2_nonpgo.exe)
	@$(call remove_file,../nullstar_mingw_avx2_pgo.exe)

-include $(DEP)
