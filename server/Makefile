JAVAC=javac
sources = $(wildcard *.java)
classes = $(sources:.java=.class)

all: ABSoftware1

ABSoftware1: $(classes)

cleam :
	rm -f *.class

%.class : %.java
	$(JAVAC) $<

jar: $(classes)
	jar cvf ABSoftware1.jar $(classes)
