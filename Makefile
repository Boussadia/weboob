core := weboob/tools/application/qt
applications := qboobmsg qhavedate qwebcontentedit qflatboob
ifeq ($(WIN32),)
	applications += qvideoob
endif

directories := $(core) $(applications:%=weboob/applications/%/ui)

.PHONY: clean all $(directories)

all: target := all
all: $(directories)

clean: target := clean
clean: $(directories)

$(directories):
	$(MAKE) -C $@ $(target)
