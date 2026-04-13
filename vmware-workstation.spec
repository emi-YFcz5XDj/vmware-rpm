Name: vmware-workstation
Version: 25H2u1
%global semantic_version 25.0.1
%global build_number 25219725
Release: %autorelease
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
# Required for setting SELinux file context
Requires: /usr/sbin/semanage
# TODO: Remove once VMware fixes their libraries
BuildRequires: patchelf

%global installer_database %{buildroot}%{_sysconfdir}/vmware-installer/database
%global iso_dir %{buildroot}%{_exec_prefix}/lib/vmware/isoimages
%global dkms_dir %{buildroot}%{_usrsrc}/%{NAME}-%{VERSION}

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
Source11: vmware-config
Source12: configure-initscript.sh
Source13: vmware-modconfig

Source14: vmware-networks-configuration.service
Source15: vmware-networks.service
Source16: vmware-usbarbitrator.service
Source17: vmware-networks.path
Source18: vmware-usbarbitrator.path

Source19: dkms.conf.in
Source20: Makefile
Source21: vmmon.patch
Source22: vmnet.patch
Source23: vmware-modules.conf

Source24: unlocker.py
Source25: efi-patches.txt
Source26: https://packages-prod.broadcom.com/tools/frozen/darwin/darwin.iso
Source27: https://packages-prod.broadcom.com/tools/frozen/darwin/darwinPre15.iso
Source28: UEFIPatch

# Warning: Running macOS guest on non Apple devices is a violation of both Apple and VMware EULA
%bcond unlocker 1

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
cd extracted
install -Dm 755 %{SOURCE12} vmware-installer/bin/configure-initscript.sh
#region Add StartupWMClass attribute to desktop files
sed -i '/^StartupNotify=.*/a StartupWMClass=vmware' 'vmware-workstation/share/applications/vmware-workstation.desktop'
sed -i '/^StartupNotify=.*/a StartupWMClass=vmplayer' 'vmware-player-app/share/applications/vmware-player.desktop'
sed -i '/^StartupNotify=.*/a StartupWMClass=vmware-netcfg' 'vmware-network-editor-ui/share/applications/vmware-netcfg.desktop'
#endregion
#region VMware upgraded bundled libxml2 without rebuilding these against it?
find \
	-type f -name 'libcroco-0.6.so.3' \
	-exec patchelf {} --replace-needed libxml2.so.2 libxml2.so.16 \; -or \
	-type f -name 'librsvg-2.so.2' \
	-exec patchelf {} --replace-needed libxml2.so.2 libxml2.so.16 \; -or \
	-type f -name 'libpixbufloader-svg.so' \
	-exec patchelf {} --replace-needed libxml2.so.2 libxml2.so.16 \;
#endregion
#region Prepare DKMS and Patch the Kernel modules
mkdir patched
sed \
	-e "s/@NAME@/%{NAME}/g" \
	-e "s/@VERSION@/%{VERSION}/g" \
	-i "%{SOURCE19}"
tar -xf 'vmware-vmx/lib/modules/source/vmmon.tar' -C 'patched'
patch -p2 --read-only=ignore --directory='patched/vmmon-only' < %{SOURCE21}
tar -xf 'vmware-vmx/lib/modules/source/vmnet.tar' -C 'patched'
patch -p2 --read-only=ignore --directory='patched/vmnet-only' < %{SOURCE22}
rm -f vmware-vmx/lib/modules/source/{vmmon,vmnet}.tar
#endregion

%install
## Replicate the install order of vmware-installer, but install VMX first because of appLoader
cd extracted
#region VMware Installer
pushd vmware-installer

installer_version=$(cat manifest.xml | grep -oPm1 "(?<=<version>)[^<]+")
installer_dir="%{_exec_prefix}/lib/vmware-installer/${installer_version}"

mkdir -p %{buildroot}/${installer_dir}
cp -r vmis* %{buildroot}/${installer_dir}/
cp -r sopython %{buildroot}/${installer_dir}/
cp -r python %{buildroot}/${installer_dir}/
cp -r cdsHelper %{buildroot}/${installer_dir}/
cp -r vmware* %{buildroot}/${installer_dir}/
cp -r bin %{buildroot}/${installer_dir}/
cp -r lib %{buildroot}/${installer_dir}/

chmod +x %{buildroot}/${installer_dir}/vmis-launcher \
	%{buildroot}/${installer_dir}/sopython/* \
	%{buildroot}/${installer_dir}/python/init.sh \
	%{buildroot}/${installer_dir}/vmware-*
mkdir -p %{buildroot}%{_bindir}
ln -s ${installer_dir}/vmware-installer %{buildroot}%{_bindir}/vmware-installer

mkdir -p %{buildroot}%{_sysconfdir}/vmware-installer
install -Dm 644 bootstrap %{buildroot}%{_sysconfdir}/vmware-installer/bootstrap
sed -i -e "s,@@VMWARE_INSTALLER@@,${installer_dir}," %{buildroot}%{_sysconfdir}/vmware-installer/bootstrap
sed -i -e "s,@@VERSION@@,%{installer_version}," %{buildroot}%{_sysconfdir}/vmware-installer/bootstrap

register_component()
{
	component="$(dirname ${PWD}/.installer)"
	component_name="$(basename $component)"
	component_version=$(cat ${component}/manifest.xml | grep -oPm1 "(?<=<version>)[^<]+")
	component_long_name=$(cat ${component}/manifest.xml | grep -oPm1 "(?<=<longName>)[^<]+")
	component_description=$(cat ${component}/manifest.xml | grep -oPm1 "(?<=<description>)[^<]+")
	component_core_id=$([ "$component_name" == "vmware-installer" ] && echo "-1" || echo "1")
	type=$([ "$component_name" == "vmware-workstation" ] && echo "0" || echo "1")

	sqlite3 %{installer_database} "INSERT INTO components(name,version,buildNumber,component_core_id,longName,description,type) \
		VALUES('$component_name','$component_version',%{build_number},$component_core_id,'$component_long_name','$component_description',$type);"

	mkdir -p %{buildroot}%{_sysconfdir}/vmware-installer/components/$component_name
	cp -r .installer/* %{buildroot}%{_sysconfdir}/vmware-installer/components/$component_name
}
touch %{installer_database}
sqlite3 %{installer_database} "CREATE TABLE settings(key VARCHAR PRIMARY KEY, value VARCHAR NOT NULL, component_name VARCHAR NOT NULL);"
sqlite3 %{installer_database} "INSERT INTO settings(key,value,component_name) VALUES('db.schemaVersion','2','vmware-installer');"
sqlite3 %{installer_database} "CREATE TABLE components(id INTEGER PRIMARY KEY, name VARCHAR NOT NULL, version VARCHAR NOT NULL, buildNumber INTEGER NOT NULL, component_core_id INTEGER NOT NULL, longName VARCHAR NOT NULL, description VARCHAR, type INTEGER NOT NULL);"
register_component
popd
#endregion
#region VMware Bootstrap
install -Dm 644 %{SOURCE9} %{buildroot}%{_sysconfdir}/vmware/bootstrap
#endregion
#region VMware Config
install -Dm 644 %{SOURCE11} %{buildroot}%{_sysconfdir}/vmware/config
sed -i -e "s,@@VERSION@@,%{semantic_version}," %{buildroot}%{_sysconfdir}/vmware/config
sed -i -e "s,@@BUILD@@,%{build_number}," %{buildroot}%{_sysconfdir}/vmware/config
sed -i -e "s,@@PREFIXDIR@@,%{_exec_prefix}," %{buildroot}%{_sysconfdir}/vmware/config
#endregion
#region VMware VMX
pushd vmware-vmx

cp -r bin/* %{buildroot}%{_bindir}/
mkdir -p %{buildroot}%{_sysconfdir}
cp -r etc/modprobe.d %{buildroot}%{_sysconfdir}/
mkdir -p %{buildroot}%{_exec_prefix}/lib/vmware/roms
cp -r roms/* %{buildroot}%{_exec_prefix}/lib/vmware/roms
cp -r sbin/* %{buildroot}%{_bindir}/

## Bundled services are not used
#cp -r etc/init.d/* %\{buildroot}%\{_exec_prefix}/lib/vmware/scripts/init/
#cp -r systemd/* %\{buildroot}%\{_exec_prefix}/lib/systemd/system/

cp -r lib/libconf %{buildroot}%{_exec_prefix}/lib/vmware/

cp -r lib/bin %{buildroot}%{_exec_prefix}/lib/vmware/
cp -r lib/lib %{buildroot}%{_exec_prefix}/lib/vmware/
cp -r lib/scripts %{buildroot}%{_exec_prefix}/lib/vmware/
cp -r lib/icu %{buildroot}%{_exec_prefix}/lib/vmware/
cp -r lib/share %{buildroot}%{_exec_prefix}/lib/vmware/
cp -r lib/modules %{buildroot}%{_exec_prefix}/lib/vmware/
cp -r lib/include %{buildroot}%{_exec_prefix}/lib/vmware/

install -Dm 644 extra/modules.xml %{buildroot}%{_exec_prefix}/lib/vmware/modules/

ln -s appLoader %{buildroot}%{_exec_prefix}/lib/vmware/bin/vmware-vmblock-fuse
ln -s %{_exec_prefix}/lib/vmware/icu %{buildroot}%{_sysconfdir}/vmware/icu

## Replace vmware-modconfig with simple error dialog
install -Dm 755 %{SOURCE13} %{buildroot}%{_bindir}/vmware-modconfig
sed -i -e "s,@@ETCDIR@@,%{_sysconfdir}/vmware," %{buildroot}%{_bindir}/vmware-modconfig

register_component
popd
#endregion
#region VMware USB Arbitrator
pushd vmware-usbarbitrator

## Use custom systemd service
#cp -r vmware-usbarbitrator/etc/init.d/* %\{buildroot}%\{_exec_prefix}/lib/vmware/scripts/init/
#install -Dm 644 vmware-usbarbitrator/systemd/vmware-USBArbitrator.service %\{buildroot}%\{_exec_prefix}/lib/systemd/system/vmware-USBArbitrator.service
install -Dm 644 %{SOURCE16} %{buildroot}%{_exec_prefix}/lib/systemd/system/vmware-usbarbitrator.service
install -Dm 644 %{SOURCE18} %{buildroot}%{_exec_prefix}/lib/systemd/system/vmware-usbarbitrator.path

cp -r bin/* %{buildroot}%{_bindir}/
ln -s appLoader %{buildroot}%{_exec_prefix}/lib/vmware/bin/vmware-usbarbitrator

register_component
popd
#endregion
#region VMware Player Setup
pushd vmware-player-setup

mkdir -p %{buildroot}%{_exec_prefix}/lib/vmware/setup
cp vmware-config %{buildroot}%{_exec_prefix}/lib/vmware/setup/

register_component
popd
#endregion
#region VMware Network Editor
pushd vmware-network-editor

cp -r lib %{buildroot}%{_exec_prefix}/lib/vmware/

register_component
popd
#endregion
#region VMware Tools for Windows Vista or later
pushd vmware-tools-windows

install -Dm 644 windows.iso %{iso_dir}/windows.iso

register_component
popd
#endregion
#region Other VMware Tools Images
install -Dm 644 %{SOURCE1} %{iso_dir}/linux.iso
install -Dm 644 %{SOURCE2} %{iso_dir}/linuxPreGlibc25.iso
install -Dm 644 %{SOURCE3} %{iso_dir}/netware.iso
install -Dm 644 %{SOURCE4} %{iso_dir}/solaris.iso
install -Dm 644 %{SOURCE5} %{iso_dir}/winPre2k.iso
install -Dm 644 %{SOURCE6} %{iso_dir}/winPreVista.iso
install -Dm 644 %{SOURCE7} %{iso_dir}/winVistaSP1.iso
install -Dm 644 %{SOURCE8} %{iso_dir}/winVistaSP2.iso

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
	sqlite3 %{installer_database} "INSERT INTO components(name,version,buildNumber,component_core_id,longName,description,type) \
		VALUES('vmware-tools-${iso}','1',%{build_number},1,'${iso}','${iso}',1);"
done

#endregion
#region VMware Player Application
pushd vmware-player-app

cp -r lib/* %{buildroot}%{_exec_prefix}/lib/vmware/
mkdir -p %{buildroot}%{_datadir}
cp -r share/* %{buildroot}%{_datadir}/
cp -r bin/* %{buildroot}%{_bindir}/
## Licences
mkdir -p %{buildroot}%{_docdir}/vmware-player
cp -r doc/* %{buildroot}%{_docdir}/vmware-player/

for target in \
	vmplayer \
	vmware-enter-serial \
	vmware-setup-helper \
	licenseTool \
	vmware-mount \
	vmware-fuseUI \
	vmware-app-control \
	vmware-zenity
do
	ln -s appLoader %{buildroot}%{_exec_prefix}/lib/vmware/bin/$target
done

ln -s %{_exec_prefix}/lib/vmware/bin/vmware-mount %{buildroot}%{_bindir}/vmware-mount
ln -s %{_exec_prefix}/lib/vmware/bin/vmware-fuseUI %{buildroot}%{_bindir}/vmware-fuseUI
ln -s %{_exec_prefix}/lib/vmware/bin/vmrest %{buildroot}%{_bindir}/vmrest

## Replace vmplayer desktop file placeholders
sed -i -e "s,@@BINARY@@,%{_bindir}/vmplayer," %{buildroot}%{_datadir}/applications/vmware-player.desktop

register_component
popd
#endregion
#region VMware OVF Tool component for Linux
pushd vmware-ovftool

mkdir -p %{buildroot}%{_exec_prefix}/lib/vmware-ovftool/

cp -r * %{buildroot}%{_exec_prefix}/lib/vmware-ovftool/
chmod 755 %{buildroot}%{_exec_prefix}/lib/vmware-ovftool/ovftool*
ln -s %{_exec_prefix}/lib/vmware-ovftool/ovftool %{buildroot}%{_bindir}/ovftool

register_component

popd
#endregion
#region VMware Network Editor User Interface
pushd vmware-network-editor-ui

cp -r share/* %{buildroot}%{_datadir}/

ln -s appLoader %{buildroot}%{_exec_prefix}/lib/vmware/bin/vmware-netcfg
ln -s %{_exec_prefix}/lib/vmware/bin/vmware-netcfg %{buildroot}%{_bindir}/vmware-netcfg

## Replace Network Editor UI desktop file placeholders
sed -i -e "s,@@BINARY@@,%{_bindir}/vmware-netcfg," %{buildroot}%{_datadir}/applications/vmware-netcfg.desktop

register_component
popd
#endregion
#region VMware VIX Core Library
pushd vmware-vix-core
mkdir -p %{buildroot}%{_exec_prefix}/lib/vmware-vix
cp -r lib/* %{buildroot}%{_exec_prefix}/lib/vmware-vix/
cp -r bin/* %{buildroot}%{_bindir}/

install -Dm 644 %{SOURCE10} %{buildroot}%{_sysconfdir}/vmware-vix/bootstrap

mkdir -p %{buildroot}%{_includedir}/vmware-vix
cp -r include/* %{buildroot}%{_includedir}/vmware-vix
## Licence and vixwrapper-config
cp -r *.txt %{buildroot}%{_exec_prefix}/lib/vmware-vix/
mkdir -p %{buildroot}%{_docdir}/vmware-vix/
cp -r doc/* %{buildroot}%{_docdir}/vmware-vix/

register_component
popd
#endregion
#region VMware VIX Workstation-17.0.0 Library
pushd vmware-vix-lib-Workstation1700
cp -r lib/* %{buildroot}%{_exec_prefix}/lib/vmware-vix/
register_component
popd
#endregion
#region VMware VProbes
pushd vmware-vprobe
cp -r bin/* %{buildroot}%{_bindir}/
cp -r lib/* %{buildroot}%{_exec_prefix}/lib/vmware/
register_component
popd
#endregion
#region VMware Workstation
pushd vmware-workstation

cp -r bin/* %{buildroot}%{_bindir}/
cp -r lib/* %{buildroot}%{_exec_prefix}/lib/vmware/
cp -r share/* %{buildroot}%{_datadir}/
cp -r man %{buildroot}%{_datadir}/

## Licences
mkdir -p %{buildroot}%{_docdir}/vmware-workstation
cp -r doc/* %{buildroot}%{_docdir}/vmware-workstation

ln -s appLoader %{buildroot}%{_exec_prefix}/lib/vmware/bin/vmware
ln -s appLoader %{buildroot}%{_exec_prefix}/lib/vmware/bin/vmware-tray
ln -s appLoader %{buildroot}%{_exec_prefix}/lib/vmware/bin/vmware-vprobe

## Replace VMware Workstation UI desktop file placeholders
sed -i -e "s,@@BINARY@@,%{_bindir}/vmware," %{buildroot}%{_datadir}/applications/vmware-workstation.desktop

## Remove bundled X11 libraries
for library in \
	%{buildroot}%{_exec_prefix}/lib/vmware/lib/* \
	%{buildroot}%{_exec_prefix}/lib/vmware-ovftool/lib*.so*
do
	library_name=$(basename "$library")
	if [[ "$library_name" == libX* || "$library_name" == libxcb* ]]; then
		rm -rf "$library"
	fi
done

register_component
popd
#endregion
#region VMWare Networks Services
install -Dm 644 %{SOURCE14} %{buildroot}%{_exec_prefix}/lib/systemd/system/vmware-networks-configuration.service
install -Dm 644 %{SOURCE15} %{buildroot}%{_exec_prefix}/lib/systemd/system/vmware-networks.service
install -Dm 644 %{SOURCE17} %{buildroot}%{_exec_prefix}/lib/systemd/system/vmware-networks.path
#endregion
#region Configure Kmods
install -Dm 644 %{SOURCE19} %{dkms_dir}/dkms.conf
install -Dm 644 %{SOURCE20} %{dkms_dir}/Makefile
cp -r patched/vmmon-only %{dkms_dir}/
cp -r patched/vmnet-only %{dkms_dir}/

install -Dm 644 %{SOURCE23} %{buildroot}%{_exec_prefix}/lib/modules-load.d/vmware.conf
#endregion
#region Enable macOS Guests
%if %{with unlocker}
	## Edit unlocker.py to operate on buildroot
	sed -i -e "s|%{_exec_prefix}/lib/vmware/|%{buildroot}%{_exec_prefix}/lib/vmware/|" %{SOURCE24}
	python3 %{SOURCE24}
	%{SOURCE28} %{buildroot}%{_exec_prefix}/lib/vmware/roms/EFI32.ROM %{SOURCE25} -o %{buildroot}%{_exec_prefix}/lib/vmware/roms/EFI32.ROM
	%{SOURCE28} %{buildroot}%{_exec_prefix}/lib/vmware/roms/EFI64.ROM %{SOURCE25} -o %{buildroot}%{_exec_prefix}/lib/vmware/roms/EFI64.ROM
	%{SOURCE28} %{buildroot}%{_exec_prefix}/lib/vmware/roms/EFI20-32.ROM %{SOURCE25} -o %{buildroot}%{_exec_prefix}/lib/vmware/roms/EFI20-32.ROM
	%{SOURCE28} %{buildroot}%{_exec_prefix}/lib/vmware/roms/EFI20-64.ROM %{SOURCE25} -o %{buildroot}%{_exec_prefix}/lib/vmware/roms/EFI20-64.ROM
	install -Dm 644 %{SOURCE26} %{iso_dir}/darwin.iso
	install -Dm 644 %{SOURCE27} %{iso_dir}/darwinPre15.iso
	for iso in \
		darwin \
		darwinPre15
	do
		sqlite3 %{installer_database} "INSERT INTO components(name,version,buildNumber,component_core_id,longName,description,type) \
			VALUES('vmware-tools-${iso}','1',%{fusion_build_number},1,'${iso}','${iso}',1);"
	done
%endif
#endregion
%check
sqlite3 %{installer_database} 'select * FROM components'
sqlite3 %{installer_database} 'select * FROM settings'
test -d %{dkms_dir}/vmmon-only
test -d %{dkms_dir}/vmnet-only
for iso in \
	windows \
	linux \
	linuxPreGlibc25 \
	netware \
	solaris \
	winPre2k \
	winPreVista \
	winVistaSP1 \
	winVistaSP2
do
	test -s %{iso_dir}/${iso}.iso
done
%if %{with unlocker}
for iso in \
	darwin \
	darwinPre15
do
	test -s %{iso_dir}/${iso}.iso
done
%endif

%post
semanage fcontext --add --type vmware_host_exec_t %{_exec_prefix}/lib/vmware/bin/vmware-usbarbitrator
restorecon %{_exec_prefix}/lib/vmware/bin/vmware-usbarbitrator
dkms add -q -m %{NAME} -v %{VERSION} --rpm_safe_upgrade
dkms install -q -m %{NAME} -v %{VERSION} --force || true

%preun
dkms remove -q -m %{NAME} -v %{VERSION} --all --rpm_safe_upgrade || true

%postun
if [ $1 -eq 0 ]; then
	semanage fcontext --delete --type vmware_host_exec_t %{_exec_prefix}/lib/vmware/bin/vmware-usbarbitrator
fi

#region files
%files
%defattr(0644, root, root, 0755)
%{_sysconfdir}/modprobe.d/modprobe-vmware-fuse.conf
%{_sysconfdir}/vmware/
%{_sysconfdir}/vmware-installer/
%ghost %{_sysconfdir}/vmware-tools/
%{_sysconfdir}/vmware-vix/
%{_includedir}/vmware-vix/
%{_exec_prefix}/lib/modules-load.d/vmware.conf
%{_exec_prefix}/lib/systemd/system/vmware-networks-configuration.service
%{_exec_prefix}/lib/systemd/system/vmware-networks.path
%{_exec_prefix}/lib/systemd/system/vmware-networks.service
%{_exec_prefix}/lib/systemd/system/vmware-usbarbitrator.path
%{_exec_prefix}/lib/systemd/system/vmware-usbarbitrator.service
%{_exec_prefix}/lib/vmware/
%{_exec_prefix}/lib/vmware-installer/
%{_exec_prefix}/lib/vmware-ovftool/
%{_exec_prefix}/lib/vmware-vix/
%{_datadir}/appdata/vmware-player.appdata.xml
%{_datadir}/appdata/vmware-workstation.appdata.xml
%{_datadir}/applications/vmware-netcfg.desktop
%{_datadir}/applications/vmware-player.desktop
%{_datadir}/applications/vmware-workstation.desktop
%{_datadir}/icons/hicolor/16x16/apps/vmware-netcfg.png
%{_datadir}/icons/hicolor/16x16/apps/vmware-player.png
%{_datadir}/icons/hicolor/16x16/apps/vmware-workstation.png
%{_datadir}/icons/hicolor/16x16/mimetypes/application-certificate.png
%{_datadir}/icons/hicolor/16x16/mimetypes/application-x-vmware-easter-egg.png
%{_datadir}/icons/hicolor/16x16/mimetypes/application-x-vmware-team.png
%{_datadir}/icons/hicolor/16x16/mimetypes/application-x-vmware-vm-clone.png
%{_datadir}/icons/hicolor/16x16/mimetypes/application-x-vmware-vm-legacy.png
%{_datadir}/icons/hicolor/16x16/mimetypes/application-x-vmware-vm.png
%{_datadir}/icons/hicolor/22x22/apps/vmware-netcfg.png
%{_datadir}/icons/hicolor/22x22/apps/vmware-player.png
%{_datadir}/icons/hicolor/22x22/apps/vmware-workstation.png
%{_datadir}/icons/hicolor/22x22/mimetypes/application-certificate.png
%{_datadir}/icons/hicolor/22x22/mimetypes/application-x-vmware-vm-clone.png
%{_datadir}/icons/hicolor/22x22/mimetypes/application-x-vmware-vm.png
%{_datadir}/icons/hicolor/24x24/apps/vmware-netcfg.png
%{_datadir}/icons/hicolor/24x24/apps/vmware-player.png
%{_datadir}/icons/hicolor/24x24/apps/vmware-workstation.png
%{_datadir}/icons/hicolor/24x24/mimetypes/application-certificate.png
%{_datadir}/icons/hicolor/24x24/mimetypes/application-x-vmware-vm-clone.png
%{_datadir}/icons/hicolor/24x24/mimetypes/application-x-vmware-vm.png
%{_datadir}/icons/hicolor/256x256/apps/vmware-netcfg.png
%{_datadir}/icons/hicolor/256x256/apps/vmware-player.png
%{_datadir}/icons/hicolor/256x256/apps/vmware-workstation.png
%{_datadir}/icons/hicolor/32x32/apps/vmware-netcfg.png
%{_datadir}/icons/hicolor/32x32/apps/vmware-player.png
%{_datadir}/icons/hicolor/32x32/apps/vmware-workstation.png
%{_datadir}/icons/hicolor/32x32/mimetypes/application-certificate.png
%{_datadir}/icons/hicolor/32x32/mimetypes/application-x-vmware-easter-egg.png
%{_datadir}/icons/hicolor/32x32/mimetypes/application-x-vmware-team.png
%{_datadir}/icons/hicolor/32x32/mimetypes/application-x-vmware-vm-clone.png
%{_datadir}/icons/hicolor/32x32/mimetypes/application-x-vmware-vm-legacy.png
%{_datadir}/icons/hicolor/32x32/mimetypes/application-x-vmware-vm.png
%{_datadir}/icons/hicolor/48x48/apps/vmware-netcfg.png
%{_datadir}/icons/hicolor/48x48/apps/vmware-player.png
%{_datadir}/icons/hicolor/48x48/apps/vmware-workstation.png
%{_datadir}/icons/hicolor/48x48/mimetypes/application-x-vmware-easter-egg.png
%{_datadir}/icons/hicolor/48x48/mimetypes/application-x-vmware-snapshot.png
%{_datadir}/icons/hicolor/48x48/mimetypes/application-x-vmware-team.png
%{_datadir}/icons/hicolor/48x48/mimetypes/application-x-vmware-vm-clone.png
%{_datadir}/icons/hicolor/48x48/mimetypes/application-x-vmware-vm-legacy.png
%{_datadir}/icons/hicolor/48x48/mimetypes/application-x-vmware-vm.png
%{_datadir}/icons/hicolor/48x48/mimetypes/application-x-vmware-vmdisk.png
%{_datadir}/icons/hicolor/48x48/mimetypes/application-x-vmware-vmfoundry.png
%{_datadir}/icons/hicolor/scalable/mimetypes/application-certificate.svg
%{_datadir}/icons/hicolor/scalable/mimetypes/application-x-vmware-easter-egg.svg
%{_datadir}/icons/hicolor/scalable/mimetypes/application-x-vmware-snapshot.svg
%{_datadir}/icons/hicolor/scalable/mimetypes/application-x-vmware-team.svg
%{_datadir}/icons/hicolor/scalable/mimetypes/application-x-vmware-vm-clone.svg
%{_datadir}/icons/hicolor/scalable/mimetypes/application-x-vmware-vm-legacy.svg
%{_datadir}/icons/hicolor/scalable/mimetypes/application-x-vmware-vm.svg
%{_datadir}/icons/hicolor/scalable/mimetypes/application-x-vmware-vmfoundry.svg
%{_datadir}/mime/packages/vmware-player.xml

%{_usrsrc}/%{NAME}-%{VERSION}/

%doc %{_datadir}/doc/vmware-vix/
%doc %{_datadir}/man/man1/vmware.1.gz
%doc %{_exec_prefix}/lib/vmware-ovftool/README.txt
%license %{_exec_prefix}/lib/vmware-installer/*/python/lib/LICENSE.txt
%license %{_exec_prefix}/lib/vmware-ovftool/open_source_licenses.txt
%license %{_exec_prefix}/lib/vmware-ovftool/vmware-eula.rtf
%license %{_exec_prefix}/lib/vmware-ovftool/vmware.eula
%license %{_exec_prefix}/lib/vmware-vix/open_source_licenses.txt
%license %{_datadir}/doc/vmware-player/open_source_licenses.txt
%license %{_datadir}/doc/vmware-player/ovftool_open_source_licenses.txt
%license %{_datadir}/doc/vmware-workstation/EULA
%license %{_datadir}/doc/vmware-workstation/open_source_licenses.txt
%license %{_datadir}/doc/vmware-workstation/ovftool_open_source_licenses.txt

%defattr(0755, -, -, -)
%{_bindir}/dictTool
%{_bindir}/ovftool
%{_bindir}/vmcli
%{_bindir}/vmnet-bridge
%{_bindir}/vmnet-dhcpd
%{_bindir}/vmnet-natd
%{_bindir}/vmnet-netifup
%{_bindir}/vmnet-sniffer
%{_bindir}/vmplayer
%{_bindir}/vmrest
%{_bindir}/vmrun
%{_bindir}/vmss2core
%{_bindir}/vmware
%{_bindir}/vmware-authd
%{_bindir}/vmware-authdlauncher
%{_bindir}/vmware-collect-host-support-info
%{_bindir}/vmware-fuseUI
%{_bindir}/vmware-gksu
%{_bindir}/vmware-installer
%{_bindir}/vmware-license-check.sh
%{_bindir}/vmware-license-enter.sh
%{_bindir}/vmware-modconfig
%{_bindir}/vmware-mount
%{_bindir}/vmware-netcfg
%{_bindir}/vmware-networks
%{_bindir}/vmware-ping
%{_bindir}/vmware-tray
%{_bindir}/vmware-usbarbitrator
%{_bindir}/vmware-vdiskmanager
%{_bindir}/vmware-vprobe
%{_exec_prefix}/lib/vmware-installer/*/bin/configure-initscript.sh
%{_exec_prefix}/lib/vmware-installer/*/vmis-launcher
%{_exec_prefix}/lib/vmware-installer/*/vmware-cds-helper
%{_exec_prefix}/lib/vmware-installer/*/vmware-installer
%{_exec_prefix}/lib/vmware-installer/*/vmware-uninstall
%{_exec_prefix}/lib/vmware-installer/*/vmware-uninstall-downgrade
%{_exec_prefix}/lib/vmware/bin/appLoader
%{_exec_prefix}/lib/vmware/bin/emmett
%{_exec_prefix}/lib/vmware/bin/fusermount
%{_exec_prefix}/lib/vmware/bin/licenseTool
%{_exec_prefix}/lib/vmware/bin/mkisofs
%{_exec_prefix}/lib/vmware/bin/mksSandbox*
%{_exec_prefix}/lib/vmware/bin/tpm2emu*
%{_exec_prefix}/lib/vmware/bin/vmplayer
%{_exec_prefix}/lib/vmware/bin/vmrest
%{_exec_prefix}/lib/vmware/bin/vmplayer
%{_exec_prefix}/lib/vmware/bin/vmrest
%{_exec_prefix}/lib/vmware/bin/vmware
%{_exec_prefix}/lib/vmware/bin/vmware-app-control
%{_exec_prefix}/lib/vmware/bin/vmware-enter-serial
%{_exec_prefix}/lib/vmware/bin/vmware-fuseUI
%{_exec_prefix}/lib/vmware/bin/vmware-mount
%{_exec_prefix}/lib/vmware/bin/vmware-netcfg
%{_exec_prefix}/lib/vmware/bin/vmware-remotemks
%{_exec_prefix}/lib/vmware/bin/vmware-setup-helper
%{_exec_prefix}/lib/vmware/bin/vmware-tray
%{_exec_prefix}/lib/vmware/bin/vmware-usbarbitrator
%{_exec_prefix}/lib/vmware/bin/vmware-vmblock-fuse
%{_exec_prefix}/lib/vmware/bin/vmware-vprobe
%{_exec_prefix}/lib/vmware/bin/vmware-zenity
%{_exec_prefix}/lib/vmware/setup/vmware-config
%{_exec_prefix}/lib/vmware/lib/libvmware-gksu.so/gksu-run-helper
%{_exec_prefix}/lib/vmware-ovftool/ovftool
%{_exec_prefix}/lib/vmware-ovftool/ovftool.bin
%{_exec_prefix}/lib/vmware-vix/setup/vmware-config

## SUID
%attr(4111, -, -) %{_exec_prefix}/lib/vmware/bin/vmware-vmx
%attr(4111, -, -) %{_exec_prefix}/lib/vmware/bin/vmware-vmx-debug
%attr(4111, -, -) %{_exec_prefix}/lib/vmware/bin/vmware-vmx-stats

#endregion

%changelog
%autochangelog
