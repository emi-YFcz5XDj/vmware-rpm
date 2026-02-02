Name: vmware-workstation
Version: 25H2
%global build_number 24995812
Release: 4%{?dist}
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

Source19: dkms.conf
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
install -Dm 644 database "%{buildroot}/etc/vmware-installer/database"
cd extracted
installer_version=$(cat "vmware-installer/manifest.xml" | grep -oPm1 "(?<=<version>)[^<]+")

# Create directories and copy most files to buildroot.
mkdir -p \
	"%{buildroot}/etc"/{pam.d,modprobe.d,vmware} \
	"%{buildroot}/usr"/{share,bin} \
	"%{buildroot}/usr/include/vmware-vix" \
	"%{buildroot}/usr/lib"/{vmware/setup,vmware-vix,vmware-ovftool,vmware-installer/"$installer_version",modules-load.d} \
	"%{buildroot}/usr/share"/{doc/vmware-vix,licenses/"%{NAME}"} \
	"%{buildroot}/var/lib/vmware/Shared VMs"
cp -r \
	vmware-workstation/share/* \
	vmware-workstation/man \
	vmware-network-editor-ui/share/* \
	vmware-player-app/share/* \
	"%{buildroot}/usr/share"
cp -r \
	vmware-workstation/bin/* \
	vmware-vmx/{,s}bin/* \
	vmware-vix-core/bin/* \
	vmware-vprobe/bin/* \
	vmware-player-app/bin/* \
	"%{buildroot}/usr/bin"
cp -r \
	vmware-workstation/lib/* \
	vmware-player-app/lib/* \
	vmware-vmx/{lib/*,roms} \
	vmware-vprobe/lib/* \
	vmware-usbarbitrator/bin \
	vmware-network-editor/lib \
	"%{buildroot}/usr/lib/vmware"
cp -r \
	vmware-player-setup/vmware-config \
	"%{buildroot}/usr/lib/vmware/setup"
cp -r \
	vmware-vix-lib-Workstation1700/lib/Workstation-17.0.0 \
	vmware-vix-core/{lib/*,vixwrapper-config.txt} \
	"%{buildroot}/usr/lib/vmware-vix"
cp -r \
	vmware-vix-core/doc/* \
	"%{buildroot}/usr/share/doc/vmware-vix"
cp -r \
	vmware-ovftool/* \
	"%{buildroot}/usr/lib/vmware-ovftool"
cp -r \
	vmware-installer/{python,sopython,vmis,vmis-launcher,vmware-installer,vmware-installer.py} \
	"%{buildroot}/usr/lib/vmware-installer/$installer_version"
cp -r \
	vmware-vix-core/include/* \
	"%{buildroot}/usr/include/vmware-vix"

# Install VMware tools images.
install -Dm 644 "vmware-tools-windows/windows.iso" "%{buildroot}/usr/lib/vmware/isos/windows.iso"
install -Dm 644 %{SOURCE1} "%{buildroot}/usr/lib/vmware/isos/linux.iso"
install -Dm 644 %{SOURCE2} "%{buildroot}/usr/lib/vmware/isos/linuxPreGlibc25.iso"
install -Dm 644 %{SOURCE3} "%{buildroot}/usr/lib/vmware/isos/netware.iso"
install -Dm 644 %{SOURCE4} "%{buildroot}/usr/lib/vmware/isos/solaris.iso"
install -Dm 644 %{SOURCE5} "%{buildroot}/usr/lib/vmware/isos/winPre2k.iso"
install -Dm 644 %{SOURCE6} "%{buildroot}/usr/lib/vmware/isos/winPreVista.iso"
install -Dm 644 %{SOURCE7} "%{buildroot}/usr/lib/vmware/isos/winVistaSP1.iso"
install -Dm 644 %{SOURCE8} "%{buildroot}/usr/lib/vmware/isos/winVistaSP2.iso"

# Install licences.
install -Dm 644 "vmware-workstation/doc/EULA" "%{buildroot}/usr/share/doc/vmware-workstation/EULA"
ln -s "/usr/share/doc/vmware-workstation/EULA" "%{buildroot}/usr/share/licenses/%{NAME}/VMware Workstation - EULA.txt"
ln -s "/usr/lib/vmware-ovftool/vmware.eula" "%{buildroot}/usr/share/licenses/%{NAME}/VMware OVF Tool - EULA.txt"
install -Dm 644 "vmware-workstation/doc"/open_source_licenses.txt "%{buildroot}/usr/share/licenses/%{NAME}/VMware Workstation open source license.txt"
install -Dm 644 "vmware-workstation/doc"/ovftool_open_source_licenses.txt "%{buildroot}/usr/share/licenses/%{NAME}/VMware OVF Tool open source license.txt"
install -Dm 644 "vmware-vix-core"/open_source_licenses.txt "%{buildroot}/usr/share/licenses/%{NAME}/VMware VIX open source license.txt"
rm "%{buildroot}/usr/lib/vmware-ovftool"/{vmware-eula.rtf,open_source_licenses.txt,manifest.xml}

# Install misc bootstrap files.
install -d -m 755 "%{buildroot}/usr/lib/vmware-installer/$installer_version"/{lib/lib,artwork}
install -Dm 755 %{SOURCE12} "%{buildroot}/usr/lib/vmware-installer/$installer_version/bin/configure-initscript.sh"
install -Dm 644 vmware-vmx/extra/modules.xml "%{buildroot}"/usr/lib/vmware/modules/modules.xml
install -Dm 644 vmware-installer/bootstrap "%{buildroot}"/etc/vmware-installer/bootstrap
install -Dm 644 %{SOURCE9} "%{buildroot}"/etc/vmware/bootstrap
install -Dm 644 %{SOURCE10} "%{buildroot}"/etc/vmware-vix/bootstrap
install -Dm 644 %{SOURCE11} "%{buildroot}"/etc/vmware/config

# TODO: split vmware-keymaps package if necessary
%if %{with keymaps}
%else
	rm -r "%{buildroot}/usr/lib/vmware/xkeymap"
%endif

# Install systemd services.
install -Dm 644 %{SOURCE14} %{buildroot}/usr/lib/systemd/system/vmware-networks-configuration.service
install -Dm 644 %{SOURCE15} %{buildroot}/usr/lib/systemd/system/vmware-networks.service
install -Dm 644 %{SOURCE16} %{buildroot}/usr/lib/systemd/system/vmware-usbarbitrator.service
install -Dm 644 %{SOURCE17} %{buildroot}/usr/lib/systemd/system/vmware-networks.path
install -Dm 644 %{SOURCE18} %{buildroot}/usr/lib/systemd/system/vmware-usbarbitrator.path

# Change permissions where necessary.
chmod +x \
	"%{buildroot}/usr/bin"/* \
	"%{buildroot}/usr/lib/vmware/bin"/* \
	"%{buildroot}/usr/lib/vmware/setup"/* \
	"%{buildroot}/usr/lib/vmware/lib"/libvmware-gksu.so/gksu-run-helper \
	"%{buildroot}/usr/lib/vmware-ovftool"/{ovftool,ovftool.bin} \
	"%{buildroot}/usr/lib/vmware-installer/$installer_version"/{vmware-installer,vmis-launcher} \
	"%{buildroot}/usr/lib/vmware-vix/setup"/*
chmod +s \
	"%{buildroot}/usr/bin"/vmware-authd \
	"%{buildroot}/usr/lib/vmware/bin"/{vmware-vmx,vmware-vmx-debug,vmware-vmx-stats}

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
	ln -s /usr/lib/vmware/bin/appLoader "%{buildroot}/usr/lib/vmware/bin/$link"
done
for link in \
	vmrest
do
	ln -s /usr/lib/vmware/bin/appLoader "%{buildroot}/usr/bin/$link"
done
for link in \
	vmware-fuseUI \
	vmware-mount \
	vmware-netcfg \
	vmware-usbarbitrator
do
	ln -s /usr/lib/vmware/bin/$link "%{buildroot}/usr/bin/$link"
done
ln -s /usr/lib/vmware/icu "%{buildroot}/etc/vmware/icu"
ln -s /usr/lib/vmware-ovftool/ovftool "%{buildroot}/usr/bin/ovftool"
ln -s /usr/lib/vmware-vix/libvixAllProducts.so "%{buildroot}/usr/lib/libvixAllProducts.so"

# Replace placeholder "variables" with real paths.
for file in \
	gtk-3.0/gdk-pixbuf.loaders
do
	sed -i 's,@@LIBCONF_DIR@@,/usr/lib/vmware/libconf,g' "%{buildroot}/usr/lib/vmware/libconf/etc/$file"
done
sed -i 's,@@BINARY@@,/usr/bin/vmware,' "%{buildroot}/usr/share/applications/vmware-workstation.desktop"
sed -i 's,@@BINARY@@,/usr/bin/vmplayer,' "%{buildroot}/usr/share/applications/vmware-player.desktop"
sed -i 's,@@BINARY@@,/usr/bin/vmware-netcfg,' "%{buildroot}/usr/share/applications/vmware-netcfg.desktop"
sed \
	-e "s/@@VERSION@@/$installer_version/" \
	-e "s,@@VMWARE_INSTALLER@@,/usr/lib/vmware-installer/$installer_version," \
	-i "%{buildroot}/etc/vmware-installer/bootstrap"

# Add StartupWMClass attribute to desktop files.
sed -i '/^StartupNotify=.*/a StartupWMClass=vmware' "%{buildroot}/usr/share/applications/vmware-workstation.desktop"
sed -i '/^StartupNotify=.*/a StartupWMClass=vmplayer' "%{buildroot}/usr/share/applications/vmware-player.desktop"
sed -i '/^StartupNotify=.*/a StartupWMClass=vmware-netcfg' "%{buildroot}/usr/share/applications/vmware-netcfg.desktop"

%if %{with unlocker}
	# Edit unlocker.py to operate on buildroot.
	sed -i -e "s|/usr/lib/vmware/|%{buildroot}/usr/lib/vmware/|" %{SOURCE23}
	python3 %{SOURCE23} > /dev/null
	%{SOURCE27} "%{buildroot}/usr/lib/vmware/roms/EFI32.ROM" %{SOURCE24} -o "%{buildroot}/usr/lib/vmware/roms/EFI32.ROM" > /dev/null
	%{SOURCE27} "%{buildroot}/usr/lib/vmware/roms/EFI64.ROM" %{SOURCE24} -o "%{buildroot}/usr/lib/vmware/roms/EFI64.ROM" > /dev/null
	%{SOURCE27} "%{buildroot}/usr/lib/vmware/roms/EFI20-32.ROM" %{SOURCE24} -o "%{buildroot}/usr/lib/vmware/roms/EFI20-32.ROM" > /dev/null
	%{SOURCE27} "%{buildroot}/usr/lib/vmware/roms/EFI20-64.ROM" %{SOURCE24} -o "%{buildroot}/usr/lib/vmware/roms/EFI20-64.ROM" > /dev/null
	install -Dm 644 %{SOURCE25} "%{buildroot}/usr/lib/vmware/isos/darwin.iso"
	install -Dm 644 %{SOURCE26} "%{buildroot}/usr/lib/vmware/isos/darwinPre15.iso"
%endif

# Define environment variables for VMware and remove kernel module tests.
install -Dm 644 %{SOURCE13} "%{buildroot}/etc/conf.d/vmware"
for program in vmware vmplayer vmware-tray; do
	sed -e '/export PRODUCT_NAME/asource /etc/conf.d/vmware' \
			-e 's/if "$BINDIR"\/vmware-modconfig --appname=.*/if true ||/' \
			-i "%{buildroot}/usr/bin/$program"
done

# Patch up the VMware kernel sources and configure kmods.
%define dkms_dir "%{buildroot}/usr/src/%{NAME}-%{VERSION}"
install -Dm 644 %{SOURCE19} "%{dkms_dir}/dkms.conf"
install -Dm 644 %{SOURCE20} "%{dkms_dir}/Makefile"
sed \
	-e "s/@PKGNAME@/%{NAME}/g" \
	-e "s/@PKGVER@/%{VERSION}/g" \
	-i "%{dkms_dir}/dkms.conf"
tar -xf "vmware-vmx/lib/modules/source/vmmon.tar" -C "%{dkms_dir}"
patch -p2 --read-only=ignore --directory="%{dkms_dir}/vmmon-only" < %{SOURCE21}
tar -xf "vmware-vmx/lib/modules/source/vmnet.tar" -C "%{dkms_dir}"
patch -p2 --read-only=ignore --directory="%{dkms_dir}/vmnet-only" < %{SOURCE22}
rm -r "%{buildroot}/usr/lib/vmware/modules/source"
install -Dm 644 "vmware-vmx/etc/modprobe.d/modprobe-vmware-fuse.conf" "%{buildroot}/etc/modprobe.d/vmware-fuse.conf"
echo -e "vmw_vmci\nvmmon" > "%{buildroot}/usr/lib/modules-load.d/vmware.conf"

%post
dkms add -m %{NAME} -v %{VERSION} -q --rpm_safe_upgrade
dkms build -m %{NAME} -v %{VERSION} -q
dkms install -m %{NAME} -v %{VERSION} -q

%preun
dkms remove -m %{NAME} -v %{VERSION} -q --all --rpm_safe_upgrade

%files
%license /usr/share/doc/%{NAME}/
%license /usr/share/licenses/%{NAME}
%doc /usr/share/man/man1/vmware.1.gz
%doc /usr/share/doc/vmware-vix/

/etc/conf.d/vmware
/etc/modprobe.d/vmware-fuse.conf
/etc/vmware-installer/
/etc/vmware-vix/bootstrap
/etc/vmware/
/usr/bin/dictTool
/usr/bin/ovftool
/usr/bin/vmcli
/usr/bin/vmnet*
/usr/bin/vmplayer
/usr/bin/vmrest
/usr/bin/vmrun
/usr/bin/vmss2core
/usr/bin/vmware*
/usr/include/vmware-vix/
/usr/lib/libvixAllProducts.so
/usr/lib/modules-load.d/vmware.conf
/usr/lib/systemd/system/vmware*
/usr/lib/vmware*
/usr/share/appdata/vmware*
/usr/share/applications/vmware*
/usr/share/icons/hicolor/16x16/apps/vmware*
/usr/share/icons/hicolor/16x16/mimetypes/application-certificate.png
/usr/share/icons/hicolor/16x16/mimetypes/application-x-vmware*
/usr/share/icons/hicolor/22x22/apps/vmware*
/usr/share/icons/hicolor/22x22/mimetypes/application-certificate.png
/usr/share/icons/hicolor/22x22/mimetypes/application-x-*
/usr/share/icons/hicolor/24x24/apps/vmware*
/usr/share/icons/hicolor/24x24/mimetypes/application-certificate.png
/usr/share/icons/hicolor/24x24/mimetypes/application-x-vmware*
/usr/share/icons/hicolor/32x32/apps/vmware*
/usr/share/icons/hicolor/32x32/mimetypes/application-certificate.png
/usr/share/icons/hicolor/32x32/mimetypes/application-x-vmware*
/usr/share/icons/hicolor/48x48/apps/vmware*
/usr/share/icons/hicolor/48x48/mimetypes/application-x-vmware*
/usr/share/icons/hicolor/256x256/apps/vmware*
/usr/share/icons/hicolor/scalable/mimetypes/application-certificate.svg
/usr/share/icons/hicolor/scalable/mimetypes/application-x-vmware*
/usr/share/mime/packages/vmware-player.xml
/usr/src/%{NAME}-%{VERSION}/

%changelog
* Mon Feb 02 2026 Alice H. <alice.hall0451+vcs@gmail.com>
- Fix DKMS, organise spec

* Mon Feb 02 2026 Alice H. <alice.hall0451+vcs@gmail.com>
- Fix database

* Sun Feb 01 2026 Alice H. <alice.hall0451+vcs@gmail.com>
- Initial Release
