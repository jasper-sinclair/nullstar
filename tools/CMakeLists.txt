cmake_minimum_required(VERSION 3.20)

project(nullstar_tools LANGUAGES CXX)

include(CTest)
find_package(Threads REQUIRED)

add_executable(embed_file embed_file.cpp)
target_compile_features(embed_file PRIVATE cxx_std_20)

add_executable(
  hash_table_probe
  hash_table_probe.cpp
  ../src/hash.cpp
)
target_compile_features(hash_table_probe PRIVATE cxx_std_23)
target_link_libraries(hash_table_probe PRIVATE Threads::Threads)

set(NULLSTAR_TOOL_OUTPUT_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../build/tools")
foreach(TARGET embed_file hash_table_probe)
  set_target_properties(${TARGET} PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${NULLSTAR_TOOL_OUTPUT_DIR}"
  )

  foreach(CONFIG Debug Release RelWithDebInfo MinSizeRel)
    string(TOUPPER "${CONFIG}" CONFIG_UPPER)
    set_target_properties(${TARGET} PROPERTIES
      "RUNTIME_OUTPUT_DIRECTORY_${CONFIG_UPPER}" "${NULLSTAR_TOOL_OUTPUT_DIR}"
    )
  endforeach()

  if(MSVC)
    target_compile_options(${TARGET} PRIVATE /W4 /permissive-)
  else()
    target_compile_options(${TARGET} PRIVATE -Wall -Wextra -Wpedantic)
  endif()

  if(MINGW)
    target_link_options(${TARGET} PRIVATE -static)
  endif()
endforeach()

add_test(NAME hash_table_probe COMMAND hash_table_probe)
