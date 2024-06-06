# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Integration code fo using SymSan as AFLplusplus custom mutator."""

import os
import shutil
import subprocess

from fuzzers.afl import fuzzer as afl_fuzzer
from fuzzers.aflplusplus import fuzzer as aflplusplus_fuzzer

# Helper library that contains important functions for building.
from fuzzers import utils

OSS_FUZZ_LIB_FUZZING_ENGINE_PATH = '/usr/lib/libFuzzingEngine.a'


def build_benchmark_symsan(env, benchmark_name):
    """Build a benchmark using fuzzer library."""
    if not env:
        env = os.environ.copy()

    # Add OSS-Fuzz environment variable for fuzzer library.
    fuzzer_lib = env['FUZZER_LIB']
    env['LIB_FUZZING_ENGINE'] = fuzzer_lib
    if os.path.exists(fuzzer_lib):
        # Make /usr/lib/libFuzzingEngine.a point to our library for OSS-Fuzz
        # so we can build projects that are using -lFuzzingEngine.
        shutil.copy(fuzzer_lib, OSS_FUZZ_LIB_FUZZING_ENGINE_PATH)

    build_script_name = 'build_' + benchmark_name + '.sh'
    build_script = os.path.join('/src/fuzzers/symsan', build_script_name)

    benchmark = os.getenv('BENCHMARK')
    fuzzer = os.getenv('FUZZER')
    print(f'Building benchmark {benchmark} with fuzzer {fuzzer}')
    subprocess.check_call(['/bin/bash', '-ex', build_script], env=env)


def is_benchmark(name):
    """Check the benchmark under built."""
    benchmark = os.getenv('BENCHMARK', None)
    return benchmark is not None and name in benchmark


def get_symsan_build_dir(target_directory):
    """Return path to SymSan target directory."""
    return os.path.join(target_directory, 'symsan')


def fix_flags(new_env):
    """Fix symsan build flags"""
    new_env['CC'] = '/usr/local/bin/ko-clang'
    new_env['CXX'] = '/usr/local/bin/ko-clang++'
    new_env['KO_CC'] = 'clang-12'
    new_env['KO_CXX'] = 'clang++-12'
    new_env['CFLAGS'] = ' '.join(utils.NO_SANITIZER_COMPAT_CFLAGS)
    cxxflags = [utils.LIBCPLUSPLUS_FLAG] + utils.NO_SANITIZER_COMPAT_CFLAGS
    os.environ['CXXFLAGS'] = ' '.join(cxxflags)
    #if is_benchmark('libpcap'):
    #    new_env['CXXFLAGS'] = '-libverbs'
    if is_benchmark('libgit'):
        new_env['CXXFLAGS'] = '-lpcre'
    if is_benchmark('file_magic'):
        new_env['CXXFLAGS'] = '-llzma'
    if is_benchmark('wireshark'):
        new_env['CXXFLAGS'] = '-llzma -licuuc'
    if is_benchmark('curl_curl_fuzzer_http'):
        new_env['SANITIZER'] = 'memory'
    if is_benchmark('libxslt_xpath'):
        new_env['SANITIZER'] = 'memory'
    if is_benchmark('openssl_x509'):
        new_env['CFLAGS'] = '-fsanitize=memory'
    if is_benchmark('openh264'):
        new_env['CXXFLAGS'] = '-fsanitize=memory'


def fix_abilist():
    """Fix abilist for symsan"""
    if is_benchmark('proj'):
        with open('/usr/local/lib/symsan/dfsan_abilist.txt',
                  'a',
                  encoding='utf-8') as abilist:
            abilist.write('fun:sqlite3_*=uninstrumented\n')
            abilist.write('fun:sqlite3_*=discard\n')
    if is_benchmark('freetype'):
        with open('/usr/local/lib/symsan/dfsan_abilist.txt',
                  'a',
                  encoding='utf-8') as abilist:
            abilist.write('fun:lzma*=uninstrumented\n')
            abilist.write('fun:lzma*=discard\n')
    if is_benchmark('libxml'):
        with open('/usr/local/lib/symsan/dfsan_abilist.txt',
                  'a',
                  encoding='utf-8') as abilist:
            abilist.write('fun:lzma_*=uninstrumented\n')
            abilist.write('fun:lzma_*=discard\n')
    if is_benchmark('libarchive'):
        with open('/usr/local/lib/symsan/dfsan_abilist.txt',
                  'a',
                  encoding='utf-8') as abilist:
            with open('/src/fuzzers/symsan/xml.abilist', 'r',
                      encoding='utf-8') as xml:
                abilist.write(xml.read())
            with open('/src/fuzzers/symsan/bz2.abilist', 'r',
                      encoding='utf-8') as bz2:
                abilist.write(bz2.read())
    #if is_benchmark('libgit'):
    #    with open('/usr/local/lib/symsan/dfsan_abilist.txt',
    #              'a',
    #              encoding='utf-8') as abilist:
    #        with open('/src/fuzzers/symsan/pcre.abilist', 'r',
    #                  encoding='utf-8') as pcre:
    #            abilist.write(pcre.read())
    #if is_benchmark('wireshark'):
    #    with open('/usr/local/lib/symsan/dfsan_abilist.txt',
    #              'a',
    #              encoding='utf-8') as abilist:
    #        with open('/src/fuzzers/symsan/gcry.abilist', 'r',
    #                  encoding='utf-8') as gcry:
    #            abilist.write(gcry.read())
    #        with open('/src/fuzzers/symsan/cares.abilist',
    #                  'r',
    #                  encoding='utf-8') as cares:
    #            abilist.write(cares.read())
    #        with open('/src/fuzzers/symsan/glib.abilist', 'r',
    #                  encoding='utf-8') as glib:
    #            abilist.write(glib.read())
    #        with open('/src/fuzzers/symsan/xml.abilist', 'r',
    #                  encoding='utf-8') as xml:
    #            abilist.write(xml.read())


def build_symsan(build_directory, src, work):
    """Build symsan track binaries."""
    symsan_build_directory = get_symsan_build_dir(build_directory)
    os.mkdir(symsan_build_directory)
    new_env = os.environ.copy()

    fix_flags(new_env)
    fix_abilist()
    new_env['FUZZER_LIB'] = '/libfuzzer-harness.o'
    new_env['OUT'] = symsan_build_directory
    new_env['KO_DONT_OPTIMIZE'] = '1'
    new_env['KO_USE_FASTGEN'] = '1'
    fuzz_target = os.getenv('FUZZ_TARGET')
    if fuzz_target:
        new_env['FUZZ_TARGET'] = os.path.join(symsan_build_directory,
                                              os.path.basename(fuzz_target))

    with utils.restore_directory(src), utils.restore_directory(work):
        if is_benchmark('freetype2_ftfuzzer'):
            build_benchmark_symsan(new_env, 'freetype2')
        elif is_benchmark('proj'):
            build_benchmark_symsan(new_env, 'proj')
        else:
            utils.build_benchmark(env=new_env)


def build():  # pylint: disable=too-many-branches,too-many-statements
    """Build benchmark."""
    # BUILD_MODES is not already supported by fuzzbench, meanwhile we provide
    # a default configuration.

    src = os.getenv('SRC')
    work = os.getenv('WORK')
    build_directory = os.environ['OUT']

    #if is_benchmark('libpcap'):
    #    os.environ['CXXFLAGS'] = os.environ['CXXFLAGS'] + ' -libverbs'
    if is_benchmark('libgit'):
        os.environ['CXXFLAGS'] = os.environ['CXXFLAGS'] + ' -lpcre'
    if is_benchmark('file_magic'):
        os.environ['CXXFLAGS'] = os.environ['CXXFLAGS'] + ' -llzma'
    if is_benchmark('wireshark'):
        os.environ['CXXFLAGS'] = os.environ['CXXFLAGS'] + ' -llzma -licuuc'

    with utils.restore_directory(src), utils.restore_directory(work):
        if is_benchmark('njs') or is_benchmark('muparser'):
            os.remove('/usr/local/lib/libc++.a')
            os.remove('/usr/local/lib/libc++abi.a')
        build_symsan(build_directory, src, work)
        aflplusplus_fuzzer.build('tracepc', 'dict2file')

    shutil.copy('/usr/local/bin/libSymSanMutator.so', os.environ['OUT'])


def fuzz(input_corpus, output_corpus, target_binary, flags=tuple(), skip=False):
    """Run fuzzer."""
    # Calculate CmpLog binary path from the instrumented target binary.
    target_binary_directory = os.path.dirname(target_binary)
    target_binary_name = os.path.basename(target_binary)
    symsan_binary = os.path.join(get_symsan_build_dir(target_binary_directory),
                                 target_binary_name)

    afl_fuzzer.prepare_fuzz_environment(input_corpus)
    # decomment this to enable libdislocator.
    # os.environ['AFL_ALIGNED_ALLOC'] = '1' # align malloc to max_align_t
    # os.environ['AFL_PRELOAD'] = '/afl/libdislocator.so'

    flags = list(flags)

    if os.path.exists('./afl++.dict'):
        flags += ['-x', './afl++.dict']

    #os.environ['AFL_IGNORE_TIMEOUTS'] = '1'
    os.environ['AFL_IGNORE_UNKNOWN_ENVS'] = '1'
    os.environ['AFL_FAST_CAL'] = '1'
    os.environ['AFL_NO_WARN_INSTABILITY'] = '1'

    os.environ['AFL_CUSTOM_MUTATOR_LIBRARY'] = 'libSymSanMutator.so'
    os.environ['SYMSAN_TARGET'] = symsan_binary
    os.environ['SYMSAN_USE_JIGSAW'] = '1'

    if not skip:
        os.environ['AFL_DISABLE_TRIM'] = '1'
        if 'ADDITIONAL_ARGS' in os.environ:
            flags += os.environ['ADDITIONAL_ARGS'].split(' ')

    print('target binary is ' + target_binary)

    afl_fuzzer.run_afl_fuzz(input_corpus,
                            output_corpus,
                            target_binary,
                            additional_flags=flags)
