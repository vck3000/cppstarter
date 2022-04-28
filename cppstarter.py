#!/usr/bin/env python3

"""
Sets up a C++ CMake project. Can be configured to include spdlog and/or gtest.

Helper script for MTRX3760.

Author: Victor Kuo
Date: 27-9-2020
"""

import sys
import os


def main():
    mode = input("New project (A) or git clone dependencies (B)? (A/B): ")

    if mode.lower() == "a":
        confirmOverwrite()

        author = input("Author: ")
        project_name = input("Project name: ")

        external = {}
        external["spdlog"] = True if input(
            "Install spglog (y/n)? ").lower() == "y" else False
        external["gtest"] = True if input(
            "Install gtest (y/n)? ").lower() == "y" else False
        external["fmt"] = True if input(
            "Install fmt (y/n)? ").lower() == "y" else False

        toGitClone = True if input(
            "Git clone external dependencies automatically (y/n)? ").lower() != "n" else False

        createFolders()
        writeCmakeListsTxt(project_name, external)
        writeMainCpp(author, external)
        writeHelloLib(author)
        writeBuildRunScript(project_name, external)
        writeGitIgnore()

        gitInit()

        if toGitClone:
            gitCloneDependencies(external)

        if external["gtest"]:
            writeGTestFiles(external)

    elif mode.lower() == "b":
        external = {}
        external["spdlog"] = True if input(
            "Install spglog (y/n)? ").lower() == "y" else False
        external["gtest"] = True if input(
            "Install gtest (y/n)? ").lower() == "y" else False
        external["fmt"] = True if input(
            "Install fmt (y/n)? ").lower() == "y" else False

        gitCloneDependencies(external)

    else:
        print("Invalid option. Stopping.")
        sys.exit()

    print("Done! Run './run.sh' to get started!")


def confirmOverwrite():
    if os.path.exists('src'):
        to_continue = input(
            "src folder detected. Are you sure you want to overwrite your files? (y/N): ")
        if to_continue.lower() != 'y':
            print("Cancelling")
            sys.exit()


def writeCmakeListsTxt(project_name, external):
    with open('./CMakeLists.txt', 'w') as f:

        f.write("""cmake_minimum_required(VERSION 3.10)

project(""" + project_name + """ VERSION 1.0)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra -Wshadow -Wnon-virtual-dtor -pedantic")

set(CMAKE_BINARY_DIR ${CMAKE_SOURCE_DIR}/bin)
set(EXECUTABLE_OUTPUT_PATH ${CMAKE_BINARY_DIR})
set(CMAKE_EXPORT_COMPILE_COMMANDS ON) # for clang to include headers

enable_testing()

add_subdirectory(lib)\n""" +
                ("add_subdirectory(test)\n" if external["gtest"] else "") +
                ("add_subdirectory(external/spdlog)\n" if external["spdlog"] else "") +
                ("add_subdirectory(external/googletest)\n" if external["gtest"] else "") +
                ("add_subdirectory(external/fmt)\n" if external["gtest"] else "") +
                """

add_executable(${CMAKE_PROJECT_NAME} ${PROJECT_SOURCE_DIR}/src/main.cpp)

target_link_libraries(${CMAKE_PROJECT_NAME} ${CMAKE_PROJECT_NAME}_lib)
target_include_directories(${CMAKE_PROJECT_NAME} PRIVATE ${CMAKE_SOURCE_DIR})
""")

    with open('./lib/CMakeLists.txt', 'w') as f:
        f.write("""cmake_minimum_required(VERSION 3.10)

set(LIBRARY_OUTPUT_PATH ${CMAKE_BINARY_DIR}/lib)

set(SOURCES 
  ${PROJECT_SOURCE_DIR}/lib/hello.cpp
)

add_library(${CMAKE_PROJECT_NAME}_lib STATIC ${SOURCES})
""" +
                ("include_directories(../external/spdlog/)\n" if external["spdlog"] else "") +
                ("include_directories(../external/fmt/)\n" if external["fmt"] else "") +
                ("\ntarget_link_libraries(${CMAKE_PROJECT_NAME}_lib" +
                    (" spdlog" if external["spdlog"] else "") +
                    (" fmt::fmt-header-only" if external["fmt"] else "") +
                    ")\n")
                )


def createFolders():
    folders = ['src', 'lib', 'external']

    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)


def writeMainCpp(author, external):
    with open('./src/main.cpp', 'w') as f:
        f.write("""/**
 * Author: """ + author + """
 */
""" +
                ("#include <spdlog/spdlog.h>\n" if external["spdlog"] else "") +
                ("#include <fmt/core.h>\n" if external["fmt"] else "") +
                """
#include "lib/hello.h"


int main()
{
  helloWorld();\n""" +
                ('  spdlog::info("Hello world using spdlog!");\n' if external["spdlog"] else "") +
                ('  fmt::print("Hello world using fmt!\\n");\n' if external["fmt"] else "") +
                """
  return 0;
}
""")


def writeHelloLib(author):
    with open('./lib/hello.cpp', 'w') as f:
        f.write("""/**
 * Author: """ + author + """
 */

#include <iostream>

int helloWorld()
{
    std::cout << "Hello world!" << std::endl;
    return 0;
}
""")

    with open('./lib/hello.h', 'w') as f:
        f.write("""/**
 * Author: """ + author + """
 */

int helloWorld();
""")


def writeBuildRunScript(project_name, external):
    with open('run.sh', 'w') as f:
        f.write("""#!/bin/bash 

build() {
  if [ ! -d "build" ]; then
    echo "Creating CMake files"
    mkdir build
    cmake -S . -B build
  fi

  cmake --build build -j 16 && make -C build """ + (f"&& ./bin/{project_name}_test" if external["gtest"] else "") + """
  if [ $? -eq "0" ]; then
    # Link the file for clang
    if [ ! -f compile_commands.json ]; then
      ln -s ./build/compile_commands.json ./
    fi
    echo -e "\\n\\nBuild successful!\\n\\n"
    return 0
  else
    echo -e "\\n\\nBuild failed.\\n\\n"
    return 1
  fi

}

run() {
  ./bin/""" + project_name + """ 
}

if [ $# -eq 0 ]; then
  echo "Usage: ./run.sh <build/run/buildrun>"
  exit 1
fi

if [ $1 = "run" ]; then 
  run

elif [ $1 = "build" ]; then
  build

elif [ $1 = "buildrun" ]; then
  build

  if [ $? -eq "0" ]; then
    echo -e "Running...\\n\\n"
    run
  fi
fi

""")

    os.system('chmod +x run.sh')


def writeGitIgnore():
    with open('.gitignore', 'w') as f:
        f.write("""bin/
build/
.clangd/

compile_commands.json
.DS_Store
""")


def writeGTestFiles(external):
    if not os.path.exists('test'):
        os.makedirs('test')

    with open('test/CMakeLists.txt', 'w') as f:
        f.write("""set(BINARY ${CMAKE_PROJECT_NAME}_test)

file(GLOB_RECURSE TEST_SOURCES LIST_DIRECTORIES false *.h *.cpp)

set(SOURCES ${TEST_SOURCES})

add_executable(${BINARY} ${TEST_SOURCES})

add_test(NAME ${BINARY} COMMAND ${BINARY})

target_link_libraries(${BINARY} PUBLIC ${CMAKE_PROJECT_NAME}_lib gtest)
target_include_directories(${BINARY} PRIVATE ${CMAKE_SOURCE_DIR})
""")

    with open('test/main.cpp', 'w') as f:
        f.write("""#include <gtest/gtest.h>
""" + ("#include <spdlog/spdlog.h>" if external["spdlog"] else "") + """
int main(int argc, char **argv)
{""" + ("\n  spdlog::set_level(spdlog::level::warn);\n" if external["spdlog"] else "") +
            """
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
""")

    with open('test/hello.cpp', 'w') as f:
        f.write("""#include "lib/hello.h"

#include <gtest/gtest.h>

TEST(HelloWorld, Simple) 
{
  EXPECT_EQ(helloWorld(), 0);
}
""")


def gitCloneDependencies(external):
    if external["spdlog"]:
        gitSubmoduleAdd(
            "spdlog", "https://github.com/gabime/spdlog.git")

    if external["gtest"]:
        gitSubmoduleAdd(
            "googletest", "https://github.com/google/googletest.git")

    if external["fmt"]:
        gitSubmoduleAdd(
            "fmt", "https://github.com/fmtlib/fmt.git")


def gitInit():
    os.system(f"git init")


def gitClone(folder, path):
    os.system(f"git clone {path} external/{folder}")


def gitSubmoduleAdd(folder, path):
    os.system(f"git submodule add --force {path} external/{folder}")


main()
