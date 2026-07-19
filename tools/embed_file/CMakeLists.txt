cmake_minimum_required(VERSION 3.20)

project(nullstar_embed_file LANGUAGES CXX)

add_executable(embed_file embed_file.cpp)
target_compile_features(embed_file PRIVATE cxx_std_20)

set(EMBED_FILE_OUTPUT_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../../build/tools")
set_target_properties(embed_file PROPERTIES
  RUNTIME_OUTPUT_DIRECTORY "${EMBED_FILE_OUTPUT_DIR}"
)

foreach(CONFIG Debug Release RelWithDebInfo MinSizeRel)
  string(TOUPPER "${CONFIG}" CONFIG_UPPER)
  set_target_properties(embed_file PROPERTIES
    "RUNTIME_OUTPUT_DIRECTORY_${CONFIG_UPPER}" "${EMBED_FILE_OUTPUT_DIR}"
  )
endforeach()

if(MSVC)
  target_compile_options(embed_file PRIVATE /W4 /permissive-)
else()
  target_compile_options(embed_file PRIVATE -Wall -Wextra -Wpedantic)
endif()

if(MINGW)
  target_link_options(embed_file PRIVATE -static)
endif()
