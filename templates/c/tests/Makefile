CPPUTEST_HOME=/usr
CPPFLAGS+=-g -I $(CPPUTEST_HOME)/include/CppUTest -I /usr/include/CppUTestExt
CXXFLAGS+=-include $(CPPUTEST_HOME)/include/CppUTest/MemoryLeakDetectorNewMacros.h
CFLAGS+=-include $(CPPUTEST_HOME)/include/CppUTest/MemoryLeakDetectorMallocMacros.h
LDLIBS=-lCppUTest -lCppUTestExt
bin=../bin
objects=
tests=main.cpp

all: $(bin)/runtests

$(bin)/%: $(objects) $(tests) | $(bin)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) $^ $(LDLIBS) -o $@

$(bin):
	mkdir -p $(bin)
