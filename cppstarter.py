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
        spdlog = True if input("Install spglog (y/N)? ").lower() == "y" else False
        gtest = True if input("Install gtest (y/N)? ").lower() == "y" else False
        toGitClone = True if input("Git clone spdlog and gtest automatically (Y/n)? ").lower() != "n" else False

        createFolders(spdlog, gtest)
        writeCmakeListsTxt(project_name, spdlog, gtest)
        writeMainCpp(author, spdlog)
        writeHelloLib(author)
        writeBuildRunScript(project_name, gtest)
        writeGitIgnore()

        gitInit()

        if toGitClone:
            gitCloneDependencies(spdlog, gtest)

        if gtest:
            writeGTestFiles(spdlog)

    elif mode.lower() == "b":
        spdlog = True if input("Install spglog (y/N)? ").lower() == "y" else False
        gtest = True if input("Install gtest (y/N)? ").lower() == "y" else False

        gitCloneDependencies(spdlog, gtest)

    else: 
        print("Invalid option. Stopping.")
        sys.exit()

    print("Done! Run './run.sh' to get started!")


def confirmOverwrite():
    if os.path.exists('src'):
        to_continue = input("src folder detected. Are you sure you want to overwrite your files? (y/N): ")
        if to_continue.lower() != 'y':
            print("Cancelling")
            sys.exit()

def writeCmakeListsTxt(project_name, spdlog, gtest):
    with open('./CMakeLists.txt', 'w') as f:

        f.write("""cmake_minimum_required(VERSION 3.10)

project(""" + project_name + """ VERSION 1.0)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -O2")

set(CMAKE_BINARY_DIR ${CMAKE_SOURCE_DIR}/bin)
set(EXECUTABLE_OUTPUT_PATH ${CMAKE_BINARY_DIR})
set(CMAKE_EXPORT_COMPILE_COMMANDS ON) # for clang to include headers

enable_testing()

add_subdirectory(lib)\n""" + 
("add_subdirectory(test)\n" if gtest else "") +
("add_subdirectory(external/spdlog)\n" if spdlog else "") +
("add_subdirectory(external/googletest)\n" if gtest else "") +
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
"""
+ 
("""
include_directories(../external/spdlog/)
target_link_libraries(${CMAKE_PROJECT_NAME}_lib spdlog)
""" if spdlog else "")
)


def createFolders(spdlog, gtest):
    folders = ['src', 'lib']

    if gtest or spdlog:
        folders.append('external')

    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)


def writeMainCpp(author, spdlog):
    with open('./src/main.cpp', 'w') as f:
        f.write("""/**
 * Author: """ + author + """
 */
""" + 
("#include <spdlog/spdlog.h>\n" if spdlog else "")
+ """
#include "lib/hello.h"

int main()
{
  helloWorld();\n""" + 
('  spdlog::info("Hello, World!");\n' if spdlog else "")
+ """
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
    std::cout << "Hello, World!" << std::endl;
    return 1;
}
""")


    with open('./lib/hello.h', 'w') as f:
        f.write("""/**
 * Author: """ + author + """
 */

int helloWorld();
""")

def writeBuildRunScript(project_name, gtest):
    with open('run.sh', 'w') as f:
        f.write("""#!/bin/bash 

build() {
  cmake -H. -Bbuild && make -C build """ + (f"&& ./bin/{project_name}_test" if gtest else "") + """
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


def writeGTestFiles(spdlog):
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
"""  + ("#include <spdlog/spdlog.h>" if spdlog else "") + """
int main(int argc, char **argv)
{"""  + ("\n  spdlog::set_level(spdlog::level::warn);\n" if spdlog else "") + """
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
""")

    with open('test/hello.cpp', 'w') as f:
        f.write("""#include "lib/hello.h"

#include <gtest/gtest.h>

TEST(HelloWorld, Simple) 
{
  EXPECT_EQ(helloWorld(), 1);
}
""")


def gitCloneDependencies(spdlog, gtest):
    if spdlog:
        gitSubmoduleAdd("spdlog", "https://github.com/gabime/spdlog.git")

    if gtest:
        gitSubmoduleAdd(
            "googletest", "https://github.com/google/googletest.git")

def gitInit():
    os.system(f"git init")

def gitClone(folder, path):
    os.system(f"git clone {path} external/{folder}")

def gitSubmoduleAdd(folder, path):
    os.system(f"git submodule add {path} external/{folder}")

main()
