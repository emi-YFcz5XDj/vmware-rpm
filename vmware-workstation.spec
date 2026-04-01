Name: vmware-workstation
Version: 25H2u1
%global build_number 25219725
Release: 1%{?dist}
Summary: VMware Workstation
License: Proprietary
URL: https://www.vmware.com
ExclusiveArch: x86_64
BuildRequires: sqlite
AutoReqProv: no
Provides: vmware = %{VERSION}-%{RELEASE}
Requires: dkms
Requires: gtkmm3.0
Requires: fuse
Requires: libcanberra
Requires: libaio
Requires: pcsc-lite
Requires: hicolor-icon-theme
# ovftool
Requires: libxcrypt-compat
# vmrun
Requires: libxml2
# Also bundled with upstream package
Requires: gtk3
Requires: gcr
# semanage
Requires: policycoreutils-python-utils

# Proprietary binary software
%global debug_package %{nil}
# Bundled libraries fail RPATH check, not much we can do here
%global __brp_check_rpaths %{nil}

Source0: https://archive.org/download/VMware-Workstation-Full-%{VERSION}-%{build_number}.%{_target_cpu}/VMware-Workstation-Full-%{VERSION}-%{build_number}.%{_target_cpu}.bundle
Source1: https://packages-prod.broadcom.com/tools/frozen/linux/linux.iso
Source2: https://packages-prod.broadcom.com/tools/frozen/linux/linuxPreGlibc25.iso
Source3: https://packages-prod.broadcom.com/tools/frozen/netware/netware.iso
Source4: https://packages-prod.broadcom.com/tools/frozen/solaris/solaris.iso
Source5: https://packages-prod.broadcom.com/tools/frozen/windows/winPre2k.iso
Source6: https://packages-prod.broadcom.com/tools/frozen/windows/winPreVista.iso
Source7: https://packages-prod.broadcom.com/tools/frozen/windows/WindowsToolsVista/SP1/windows.iso#/winVistaSP1.iso
Source8: https://packages-prod.broadcom.com/tools/frozen/windows/WindowsToolsVista/SP2/windows.iso#/winVistaSP2.iso

Source9: vmware-bootstrap
Source10: vmware-vix-bootstrap
Source11: config
Source12: configure-initscript.sh
Source13: vmware-environment.sh

Source14: vmware-networks-configuration.service
Source15: vmware-networks.service
Source16: vmware-usbarbitrator.service
Source17: vmware-networks.path
Source18: vmware-usbarbitrator.path

Source19: dkms.conf.in
Source20: Makefile
Source21: vmmon.patch
Source22: vmnet.patch

Source23: unlocker.py
Source24: efi-patches.txt
Source25: https://packages-prod.broadcom.com/tools/frozen/darwin/darwin.iso
Source26: https://packages-prod.broadcom.com/tools/frozen/darwin/darwinPre15.iso
Source27: UEFIPatch

%bcond keymaps 1
# Warning: Running macOS guest on non Apple devices is a violation of both Apple and VMware EULA
%bcond unlocker 0

%if %{with unlocker}
BuildRequires: python3
# EPEL
BuildRequires: qt5-qtbase
%global fusion_version 13.5.2
%global fusion_build_number 23775688
%endif

%description
The industry standard for running multiple operating systems as virtual
machines on a single computer. Snatched from AUR for the most part.

%prep
chmod +x %{SOURCE0}
%{SOURCE0} --extract extracted

%build
# Create a database with the list of guest tools to avoid on-demand download
touch database
sqlite3 database "CREATE TABLE settings(key VARCHAR PRIMARY KEY, value VARCHAR NOT NULL, component_name VARCHAR NOT NULL);"
sqlite3 database "INSERT INTO settings(key,value,component_name) VALUES('db.schemaVersion','2','vmware-installer');"
sqlite3 database "CREATE TABLE components(id INTEGER PRIMARY KEY, name VARCHAR NOT NULL, version VARCHAR NOT NULL, buildNumber INTEGER NOT NULL, component_core_id INTEGER NOT NULL, longName VARCHAR NOT NULL, description VARCHAR, type INTEGER NOT NULL);"

iso_version=$(cat "extracted/vmware-tools-windows/manifest.xml" | grep -oPm1 "(?<=<version>)[^<]+")
sqlite3 database "INSERT INTO components(name,version,buildNumber,component_core_id,longName,description,type) \
	VALUES('vmware-tools-windows','$iso_version',%{build_number},1,'windows','windows',1);"
for iso in \
	linux \
	linuxPreGlibc25 \
	netware \
	solaris \
	winPre2k \
	winPreVista \
	winVistaSP1 \
	winVistaSP2
do
	sqlite3 database "INSERT INTO components(name,version,buildNumber,component_core_id,longName,description,type) \
		VALUES('vmware-tools-$iso','1',%{build_number},1,'$iso','$iso',1);"
done
%if %{with unlocker}
	for iso in \
		darwin \
		darwinPre15
	do
		sqlite3 database "INSERT INTO components(name,version,buildNumber,component_core_id,longName,description,type) \
			VALUES('vmware-tools-$iso','1',%{fusion_build_number},1,'$iso','$iso',1);"
	done
%endif

%install
install -Dm 644 database "%{buildroot}%{_sysconfdir}/vmware-installer/database"
cd extracted
installer_version=$(cat "vmware-installer/manifest.xml" | grep -oPm1 "(?<=<version>)[^<]+")

# Create directories and copy most files to buildroot.
mkdir -p \
	"%{buildroot}%{_sysconfdir}"/{pam.d,modprobe.d,vmware} \
	"%{buildroot}%{_exec_prefix}"/{share,bin} \
	"%{buildroot}%{_includedir}/vmware-vix" \
	"%{buildroot}%{_exec_prefix}/lib"/{vmware/setup,vmware-vix,vmware-ovftool,vmware-installer/"$installer_version",modules-load.d} \
	"%{buildroot}%{_datadir}"/{doc/vmware-vix,licenses/"%{NAME}"} \
	"%{buildroot}%{_sharedstatedir}/vmware/Shared VMs"
cp -r \
	vmware-workstation/share/* \
	vmware-workstation/man \
	vmware-network-editor-ui/share/* \
	vmware-player-app/share/* \
	"%{buildroot}%{_datadir}"
cp -r \
	vmware-workstation/bin/* \
	vmware-vmx/{,s}bin/* \
	vmware-vix-core/bin/* \
	vmware-vprobe/bin/* \
	vmware-player-app/bin/* \
	"%{buildroot}%{_bindir}"
cp -r \
	vmware-workstation/lib/* \
	vmware-player-app/lib/* \
	vmware-vmx/{lib/*,roms} \
	vmware-vprobe/lib/* \
	vmware-usbarbitrator/bin \
	vmware-network-editor/lib \
	"%{buildroot}%{_exec_prefix}/lib/vmware"
cp -r \
	vmware-player-setup/vmware-config \
	"%{buildroot}%{_exec_prefix}/lib/vmware/setup"
cp -r \
	vmware-vix-lib-Workstation1700/lib/Workstation-17.0.0 \
	vmware-vix-core/{lib/*,vixwrapper-config.txt} \
	"%{buildroot}%{_exec_prefix}/lib/vmware-vix"
cp -r \
	vmware-vix-core/doc/* \
	"%{buildroot}%{_docdir}/vmware-vix"
cp -r \
	vmware-ovftool/* \
	"%{buildroot}%{_exec_prefix}/lib/vmware-ovftool"
cp -r \
	vmware-installer/{python,sopython,vmis,vmis-launcher,vmware-installer,vmware-installer.py} \
	"%{buildroot}%{_exec_prefix}/lib/vmware-installer/$installer_version"
cp -r \
	vmware-vix-core/include/* \
	"%{buildroot}%{_includedir}/vmware-vix"

# Install VMware tools images.
install -Dm 644 "vmware-tools-windows/windows.iso" "%{buildroot}%{_exec_prefix}/lib/vmware/isos/windows.iso"
install -Dm 644 %{SOURCE1} "%{buildroot}%{_exec_prefix}/lib/vmware/isos/linux.iso"
install -Dm 644 %{SOURCE2} "%{buildroot}%{_exec_prefix}/lib/vmware/isos/linuxPreGlibc25.iso"
install -Dm 644 %{SOURCE3} "%{buildroot}%{_exec_prefix}/lib/vmware/isos/netware.iso"
install -Dm 644 %{SOURCE4} "%{buildroot}%{_exec_prefix}/lib/vmware/isos/solaris.iso"
install -Dm 644 %{SOURCE5} "%{buildroot}%{_exec_prefix}/lib/vmware/isos/winPre2k.iso"
install -Dm 644 %{SOURCE6} "%{buildroot}%{_exec_prefix}/lib/vmware/isos/winPreVista.iso"
install -Dm 644 %{SOURCE7} "%{buildroot}%{_exec_prefix}/lib/vmware/isos/winVistaSP1.iso"
install -Dm 644 %{SOURCE8} "%{buildroot}%{_exec_prefix}/lib/vmware/isos/winVistaSP2.iso"

# Install licences.
install -Dm 644 "vmware-workstation/doc/EULA" "%{buildroot}%{_docdir}/vmware-workstation/EULA"
ln -s "%{_docdir}/vmware-workstation/EULA" "%{buildroot}%{_datadir}/licenses/%{NAME}/VMware Workstation - EULA.txt"
ln -s "%{_exec_prefix}/lib/vmware-ovftool/vmware.eula" "%{buildroot}%{_datadir}/licenses/%{NAME}/VMware OVF Tool - EULA.txt"
install -Dm 644 "vmware-workstation/doc"/open_source_licenses.txt "%{buildroot}%{_datadir}/licenses/%{NAME}/VMware Workstation open source license.txt"
install -Dm 644 "vmware-workstation/doc"/ovftool_open_source_licenses.txt "%{buildroot}%{_datadir}/licenses/%{NAME}/VMware OVF Tool open source license.txt"
install -Dm 644 "vmware-vix-core"/open_source_licenses.txt "%{buildroot}%{_datadir}/licenses/%{NAME}/VMware VIX open source license.txt"
rm "%{buildroot}%{_exec_prefix}/lib/vmware-ovftool"/{vmware-eula.rtf,open_source_licenses.txt,manifest.xml}

# Install misc bootstrap files.
install -d -m 755 "%{buildroot}%{_exec_prefix}/lib/vmware-installer/$installer_version"/{lib/lib,artwork}
install -Dm 755 %{SOURCE12} "%{buildroot}%{_exec_prefix}/lib/vmware-installer/$installer_version/bin/configure-initscript.sh"
install -Dm 644 vmware-vmx/extra/modules.xml "%{buildroot}"%{_exec_prefix}/lib/vmware/modules/modules.xml
install -Dm 644 vmware-installer/bootstrap "%{buildroot}"%{_sysconfdir}/vmware-installer/bootstrap
install -Dm 644 %{SOURCE9} "%{buildroot}"%{_sysconfdir}/vmware/bootstrap
install -Dm 644 %{SOURCE10} "%{buildroot}"%{_sysconfdir}/vmware-vix/bootstrap
install -Dm 644 %{SOURCE11} "%{buildroot}"%{_sysconfdir}/vmware/config

# TODO: split vmware-keymaps package if necessary
%if %{with keymaps}
%else
	rm -r "%{buildroot}%{_exec_prefix}/lib/vmware/xkeymap"
%endif

# Install systemd services.
# FIXME: Fix USB arbitrator SELinux context issue
install -Dm 644 %{SOURCE14} %{buildroot}%{_exec_prefix}/lib/systemd/system/vmware-networks-configuration.service
install -Dm 644 %{SOURCE15} %{buildroot}%{_exec_prefix}/lib/systemd/system/vmware-networks.service
install -Dm 644 %{SOURCE16} %{buildroot}%{_exec_prefix}/lib/systemd/system/vmware-usbarbitrator.service
install -Dm 644 %{SOURCE17} %{buildroot}%{_exec_prefix}/lib/systemd/system/vmware-networks.path
install -Dm 644 %{SOURCE18} %{buildroot}%{_exec_prefix}/lib/systemd/system/vmware-usbarbitrator.path

# Change permissions where necessary.
chmod +x \
	"%{buildroot}%{_bindir}"/* \
	"%{buildroot}%{_exec_prefix}/lib/vmware/bin"/* \
	"%{buildroot}%{_exec_prefix}/lib/vmware/setup"/* \
	"%{buildroot}%{_exec_prefix}/lib/vmware/lib"/libvmware-gksu.so/gksu-run-helper \
	"%{buildroot}%{_exec_prefix}/lib/vmware-ovftool"/{ovftool,ovftool.bin} \
	"%{buildroot}%{_exec_prefix}/lib/vmware-installer/$installer_version"/{vmware-installer,vmis-launcher} \
	"%{buildroot}%{_exec_prefix}/lib/vmware-vix/setup"/*
chmod +s \
	"%{buildroot}%{_bindir}"/vmware-authd \
	"%{buildroot}%{_exec_prefix}/lib/vmware/bin"/{vmware-vmx,vmware-vmx-debug,vmware-vmx-stats}

# Add symlinks the installer would create.
for link in \
	licenseTool \
	vmplayer \
	vmware \
	vmware-app-control \
	vmware-enter-serial \
	vmware-fuseUI \
	vmware-gksu \
	vmware-modconfig \
	vmware-modconfig-console \
	vmware-mount \
	vmware-netcfg \
	vmware-setup-helper \
	vmware-tray \
	vmware-vmblock-fuse \
	vmware-vprobe \
	vmware-zenity
do
	ln -s %{_exec_prefix}/lib/vmware/bin/appLoader "%{buildroot}%{_exec_prefix}/lib/vmware/bin/$link"
done
for link in \
	vmrest
do
	ln -s %{_exec_prefix}/lib/vmware/bin/appLoader "%{buildroot}%{_bindir}/$link"
done
for link in \
	vmware-fuseUI \
	vmware-mount \
	vmware-netcfg \
	vmware-usbarbitrator
do
	ln -s %{_exec_prefix}/lib/vmware/bin/$link "%{buildroot}%{_bindir}/$link"
done
ln -s %{_exec_prefix}/lib/vmware/icu "%{buildroot}%{_sysconfdir}/vmware/icu"
ln -s %{_exec_prefix}/lib/vmware-ovftool/ovftool "%{buildroot}%{_bindir}/ovftool"
ln -s %{_exec_prefix}/lib/vmware-vix/libvixAllProducts.so "%{buildroot}%{_exec_prefix}/lib/libvixAllProducts.so"

# Replace placeholder "variables" with real paths.
for file in \
	gtk-3.0/gdk-pixbuf.loaders
do
	sed -i 's,@@LIBCONF_DIR@@,%{_exec_prefix}/lib/vmware/libconf,g' "%{buildroot}%{_exec_prefix}/lib/vmware/libconf%{_sysconfdir}/$file"
done
sed -i 's,@@BINARY@@,%{_bindir}/vmware,' "%{buildroot}%{_datadir}/applications/vmware-workstation.desktop"
sed -i 's,@@BINARY@@,%{_bindir}/vmplayer,' "%{buildroot}%{_datadir}/applications/vmware-player.desktop"
sed -i 's,@@BINARY@@,%{_bindir}/vmware-netcfg,' "%{buildroot}%{_datadir}/applications/vmware-netcfg.desktop"
sed \
	-e "s/@@VERSION@@/$installer_version/" \
	-e "s,@@VMWARE_INSTALLER@@,%{_exec_prefix}/lib/vmware-installer/$installer_version," \
	-i "%{buildroot}%{_sysconfdir}/vmware-installer/bootstrap"

# Add StartupWMClass attribute to desktop files.
sed -i '/^StartupNotify=.*/a StartupWMClass=vmware' "%{buildroot}%{_datadir}/applications/vmware-workstation.desktop"
sed -i '/^StartupNotify=.*/a StartupWMClass=vmplayer' "%{buildroot}%{_datadir}/applications/vmware-player.desktop"
sed -i '/^StartupNotify=.*/a StartupWMClass=vmware-netcfg' "%{buildroot}%{_datadir}/applications/vmware-netcfg.desktop"

%if %{with unlocker}
	# Edit unlocker.py to operate on buildroot.
	sed -i -e "s|%{_exec_prefix}/lib/vmware/|%{buildroot}%{_exec_prefix}/lib/vmware/|" %{SOURCE23}
	python3 %{SOURCE23} > /dev/null
	%{SOURCE27} "%{buildroot}%{_exec_prefix}/lib/vmware/roms/EFI32.ROM" %{SOURCE24} -o "%{buildroot}%{_exec_prefix}/lib/vmware/roms/EFI32.ROM" > /dev/null
	%{SOURCE27} "%{buildroot}%{_exec_prefix}/lib/vmware/roms/EFI64.ROM" %{SOURCE24} -o "%{buildroot}%{_exec_prefix}/lib/vmware/roms/EFI64.ROM" > /dev/null
	%{SOURCE27} "%{buildroot}%{_exec_prefix}/lib/vmware/roms/EFI20-32.ROM" %{SOURCE24} -o "%{buildroot}%{_exec_prefix}/lib/vmware/roms/EFI20-32.ROM" > /dev/null
	%{SOURCE27} "%{buildroot}%{_exec_prefix}/lib/vmware/roms/EFI20-64.ROM" %{SOURCE24} -o "%{buildroot}%{_exec_prefix}/lib/vmware/roms/EFI20-64.ROM" > /dev/null
	install -Dm 644 %{SOURCE25} "%{buildroot}%{_exec_prefix}/lib/vmware/isos/darwin.iso"
	install -Dm 644 %{SOURCE26} "%{buildroot}%{_exec_prefix}/lib/vmware/isos/darwinPre15.iso"
%endif

# Define environment variables for VMware and remove kernel module tests.
install -Dm 644 %{SOURCE13} "%{buildroot}%{_sysconfdir}/conf.d/vmware"
for program in vmware vmplayer vmware-tray; do
	sed -e '/export PRODUCT_NAME/asource %{_sysconfdir}/conf.d/vmware' \
			-e 's/if "$BINDIR"\/vmware-modconfig --appname=.*/if true ||/' \
			-i "%{buildroot}%{_bindir}/$program"
done

# Patch up the VMware kernel sources and configure kmods.
%define dkms_dir "%{buildroot}%{_usrsrc}/%{NAME}-%{VERSION}"
install -Dm 644 %{SOURCE19} "%{dkms_dir}/dkms.conf"
install -Dm 644 %{SOURCE20} "%{dkms_dir}/Makefile"
sed \
	-e "s/@NAME@/%{NAME}/g" \
	-e "s/@VERSION@/%{VERSION}/g" \
	-i "%{dkms_dir}/dkms.conf"
tar -xf "vmware-vmx/lib/modules/source/vmmon.tar" -C "%{dkms_dir}"
patch -p2 --read-only=ignore --directory="%{dkms_dir}/vmmon-only" < %{SOURCE21}
tar -xf "vmware-vmx/lib/modules/source/vmnet.tar" -C "%{dkms_dir}"
patch -p2 --read-only=ignore --directory="%{dkms_dir}/vmnet-only" < %{SOURCE22}
rm -r "%{buildroot}%{_exec_prefix}/lib/vmware/modules/source"
install -Dm 644 "vmware-vmx%{_sysconfdir}/modprobe.d/modprobe-vmware-fuse.conf" "%{buildroot}%{_sysconfdir}/modprobe.d/vmware-fuse.conf"
echo -e "vmw_vmci\nvmmon" > "%{buildroot}%{_exec_prefix}/lib/modules-load.d/vmware.conf"

%check
sqlite3 "%{buildroot}%{_sysconfdir}/vmware-installer/database" 'select * FROM components'
[ -x "%{buildroot}%{_bindir}/vmware" ] || false

%post
semanage fcontext --add --type vmware_host_exec_t '%{_exec_prefix}/lib/vmware/bin/vmware-usbarbitrator' 2> /dev/null
restorecon '%{_exec_prefix}/lib/vmware/bin/vmware-usbarbitrator'
dkms add -q -m %{NAME} -v %{VERSION} --rpm_safe_upgrade
dkms install -q -m %{NAME} -v %{VERSION} --all --force || true

%preun
dkms remove -q -m %{NAME} -v %{VERSION} --all --rpm_safe_upgrade || true

%postun
if [ $1 -eq 0 ]; then
	semanage fcontext --delete --type vmware_host_exec_t '%{_exec_prefix}/lib/vmware/bin/vmware-usbarbitrator' 2> /dev/null
fi

%files
%license %{_docdir}/%{NAME}/
%license %{_datadir}/licenses/%{NAME}
%doc %{_mandir}/man1/vmware.1.gz
%doc %{_docdir}/vmware-vix/

%{_sysconfdir}/conf.d/vmware
%{_sysconfdir}/modprobe.d/vmware-fuse.conf
%{_sysconfdir}/vmware-installer/
%{_sysconfdir}/vmware-vix/bootstrap
%{_sysconfdir}/vmware/
%{_bindir}/dictTool
%{_bindir}/ovftool
%{_bindir}/vmcli
%{_bindir}/vmnet*
%{_bindir}/vmplayer
%{_bindir}/vmrest
%{_bindir}/vmrun
%{_bindir}/vmss2core
%{_bindir}/vmware*
%{_includedir}/vmware-vix/
%{_exec_prefix}/lib/libvixAllProducts.so
%{_exec_prefix}/lib/modules-load.d/vmware.conf
%{_exec_prefix}/lib/systemd/system/vmware*
%{_exec_prefix}/lib/vmware*
%{_datadir}/appdata/vmware*
%{_datadir}/applications/vmware*
%{_datadir}/icons/hicolor/16x16/apps/vmware*
%{_datadir}/icons/hicolor/16x16/mimetypes/application-certificate.png
%{_datadir}/icons/hicolor/16x16/mimetypes/application-x-vmware*
%{_datadir}/icons/hicolor/22x22/apps/vmware*
%{_datadir}/icons/hicolor/22x22/mimetypes/application-certificate.png
%{_datadir}/icons/hicolor/22x22/mimetypes/application-x-*
%{_datadir}/icons/hicolor/24x24/apps/vmware*
%{_datadir}/icons/hicolor/24x24/mimetypes/application-certificate.png
%{_datadir}/icons/hicolor/24x24/mimetypes/application-x-vmware*
%{_datadir}/icons/hicolor/32x32/apps/vmware*
%{_datadir}/icons/hicolor/32x32/mimetypes/application-certificate.png
%{_datadir}/icons/hicolor/32x32/mimetypes/application-x-vmware*
%{_datadir}/icons/hicolor/48x48/apps/vmware*
%{_datadir}/icons/hicolor/48x48/mimetypes/application-x-vmware*
%{_datadir}/icons/hicolor/256x256/apps/vmware*
%{_datadir}/icons/hicolor/scalable/mimetypes/application-certificate.svg
%{_datadir}/icons/hicolor/scalable/mimetypes/application-x-vmware*
%{_datadir}/mime/packages/vmware-player.xml
%{_usrsrc}/%{NAME}-%{VERSION}/

%changelog
* Wed Apr 01 2026 Alice H. <alice.hall0451+vcs@gmail.com> - 25h2u1-1
- Update VMware, fix USB Arbitrator file context

* Mon Mar 16 2026 Alice H. <alice.hall0451+vcs@gmail.com>
- Suppress DKMS dracut error like NVIDIA and OpenZFS

* Mon Feb 02 2026 Alice H. <alice.hall0451+vcs@gmail.com>
- Fix DKMS, organise spec

* Mon Feb 02 2026 Alice H. <alice.hall0451+vcs@gmail.com>
- Fix database

* Sun Feb 01 2026 Alice H. <alice.hall0451+vcs@gmail.com>
- Initial Release
