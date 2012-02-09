LIBEXECDIR=/usr/libexec/vdsm
HOOKSDIR=$(LIBEXECDIR)/hooks

all:

install:
	mkdir -p $(PREFIX)$(HOOKSDIR)/before_vm_start
	mkdir -p $(PREFIX)$(HOOKSDIR)/before_vm_migrate_destination
	mkdir -p $(PREFIX)/etc/sudoers.d
	cp before_vm_start.py $(PREFIX)$(HOOKSDIR)/before_vm_start/50_floppyinject
	cp before_vm_migrate_destination.py $(PREFIX)$(HOOKSDIR)/before_vm_migrate_destination/50_floppyinject
	cp sudoers.vdsm_hook_floppyinject $(PREFIX)/etc/sudoers.d/50_vdsm_hook_floppyinject


clean:
	$(RM) *~ *.pyc
