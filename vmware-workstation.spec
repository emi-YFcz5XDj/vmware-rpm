Name: vmware-workstation
Version: 26H1
%define semantic_version 26.0.0
%define build_number 25388281
%define kernel 6.12.0-264.16.1.el10_3
Release: %autorelease
Summary: Desktop Hypervisor
License: Proprietary
URL: https://www.vmware.com
ExclusiveArch: x86_64
BuildRequires: sqlite
AutoReqProv: no
Provides: vmware = %{VERSION}-%{RELEASE}
Requires: kmod-vmware = %{VERSION}-%{lua: print((rpm.expand('%{kernel}'):gsub('-', '~'):gsub('.el.*', '')))}~%{RELEASE}
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
Requires(post): %{_sbindir}/semanage
Requires(postun): %{_sbindir}/semanage
Requires(post): %{_sbindir}/restorecon

%define installer_database %{buildroot}%{_sysconfdir}/vmware-installer/database
%define iso_dir %{buildroot}%{_exec_prefix}/lib/vmware/isoimages

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

%bcond vista_sp1 0
%if %{with vista_sp1}
Source7: https://packages-prod.broadcom.com/tools/frozen/windows/WindowsToolsVista/SP1/windows.iso#/winVistaSP1.iso
%else
Source7: https://packages-prod.broadcom.com/tools/frozen/windows/WindowsToolsVista/SP2/windows.iso#/winVistaSP2.iso
%endif

Source8: vmware-bootstrap
Source9: vmware-vix-bootstrap
Source10: vmware-config
Source11: configure-initscript.sh
Source12: vmware-modconfig

Source13: vmware-networks-configuration.service
Source14: vmware-networks.service
Source15: vmware-usbarbitrator.service
Source16: vmware-networks.path
Source17: vmware-usbarbitrator.path

Source20: vmmon.patch
Source21: vmnet.patch
Source22: vmware-modules.conf

# Warning: Running macOS guest on non Apple devices is a violation of both Apple and VMware EULA
%bcond unlocker 1

%if %{with unlocker}
Source23: unlocker.py
Source24: efi-patches.txt
Source25: https://packages-prod.broadcom.com/tools/frozen/darwin/darwin.iso
Source26: https://packages-prod.broadcom.com/tools/frozen/darwin/darwinPre15.iso
Source27: UEFIPatch

BuildRequires: %{__python3}
# EPEL
BuildRequires: qt5-qtbase
%define fusion_version 13.5.2
%define fusion_build_number 23775688
%endif

%description
Run Windows, Linux and BSD virtual machines on a Windows or Linux desktop
with VMware Workstation Pro, the industry standard desktop hypervisor.

%package -n kmod-vmware
%define key /etc/pki/pesign/secure-boot.priv
%define cert /etc/pki/pesign/secure-boot.cert

Release: %{lua: print((rpm.expand('%{kernel}'):gsub('-', '~'):gsub('.el.*', '')))}~%{RELEASE}
License: GPL-2.0-only
Summary: VMware Kernel Modules

BuildRequires:	kernel-rpm-macros
BuildRequires:	redhat-rpm-config
BuildRequires:	kernel-modules-uname-r = %{kernel}.%{_arch}
BuildRequires:	kernel-devel-uname-r = %{kernel}.%{_arch}
BuildRequires:	kernel-abi-stablelists = %{kernel}
Provides:	installonlypkg(kernel-module)
Provides:	kernel-modules >= %{kernel}.%{_arch}

Requires:	kernel-uname-r >= %{kernel}.%{_arch}
Requires(post):	(kernel-devel-uname-r = %{kernel}.%{_arch} or kernel-devel-sign-only = %{kernel}.%{_arch})
Requires(post): xz
Requires(posttrans):	%{_sbindir}/depmod
Requires(postuntrans):	%{_sbindir}/depmod
Requires(posttrans):	%{_sbindir}/weak-modules
Requires(postuntrans):	%{_sbindir}/weak-modules
Requires(posttrans):	%{_bindir}/sort
Requires(postuntrans):	%{_bindir}/sort

%description -n kmod-vmware
This package provides the vmmon and vmnet kernel modules.

%prep
chmod +x %{SOURCE0}
%{SOURCE0} --extract extracted
cd extracted
%{__install} -Dm 755 %{SOURCE11} vmware-installer/bin/configure-initscript.sh
#region Add StartupWMClass attribute to desktop files
sed -i '/^StartupNotify=.*/a StartupWMClass=vmware' 'vmware-workstation/share/applications/vmware-workstation.desktop'
sed -i '/^StartupNotify=.*/a StartupWMClass=vmware-netcfg' 'vmware-network-editor-ui/share/applications/vmware-netcfg.desktop'
#endregion
#region Patch the Kernel modules
mkdir patched
tar -xf 'vmware-vmx/lib/modules/source/vmmon.tar' -C 'patched'
patch -p2 --read-only=ignore --directory='patched/vmmon-only' < %{SOURCE20}
tar -xf 'vmware-vmx/lib/modules/source/vmnet.tar' -C 'patched'
patch -p2 --read-only=ignore --directory='patched/vmnet-only' < %{SOURCE21}
rm -f vmware-vmx/lib/modules/source/{vmmon,vmnet}.tar
#endregion

%build
cd extracted/patched
for module in \
	vmmon-only \
	vmnet-only
do
	%{__make} -j %{getncpus} KVERSION=%{kernel}.%{_arch} -C $module
done

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
%{__install} -Dm 644 bootstrap %{buildroot}%{_sysconfdir}/vmware-installer/bootstrap
sed -i -e "s,@@VMWARE_INSTALLER@@,${installer_dir}," %{buildroot}%{_sysconfdir}/vmware-installer/bootstrap
sed -i -e "s,@@VERSION@@,${installer_version}," %{buildroot}%{_sysconfdir}/vmware-installer/bootstrap

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
%{__install} -Dm 644 %{SOURCE8} %{buildroot}%{_sysconfdir}/vmware/bootstrap
#endregion
#region VMware Config
%{__install} -Dm 644 %{SOURCE10} %{buildroot}%{_sysconfdir}/vmware/config
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

%{__install} -Dm 644 extra/modules.xml %{buildroot}%{_exec_prefix}/lib/vmware/modules/

ln -s appLoader %{buildroot}%{_exec_prefix}/lib/vmware/bin/vmware-vmblock-fuse
ln -s %{_exec_prefix}/lib/vmware/icu %{buildroot}%{_sysconfdir}/vmware/icu

## Replace vmware-modconfig with simple error dialog
%{__install} -Dm 755 %{SOURCE12} %{buildroot}%{_bindir}/vmware-modconfig
sed -i -e "s,@@ETCDIR@@,%{_sysconfdir}/vmware," %{buildroot}%{_bindir}/vmware-modconfig

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
#region VMware USB Arbitrator
pushd vmware-usbarbitrator

## Use custom systemd service
#cp -r vmware-usbarbitrator/etc/init.d/* %\{buildroot}%\{_exec_prefix}/lib/vmware/scripts/init/
#%{__install} -Dm 644 vmware-usbarbitrator/systemd/vmware-USBArbitrator.service %\{buildroot}%\{_exec_prefix}/lib/systemd/system/vmware-USBArbitrator.service
%{__install} -Dm 644 %{SOURCE15} %{buildroot}%{_exec_prefix}/lib/systemd/system/vmware-usbarbitrator.service
%{__install} -Dm 644 %{SOURCE17} %{buildroot}%{_exec_prefix}/lib/systemd/system/vmware-usbarbitrator.path

cp -r bin/* %{buildroot}%{_bindir}/
ln -s appLoader %{buildroot}%{_exec_prefix}/lib/vmware/bin/vmware-usbarbitrator

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

%{__install} -Dm 644 windows.iso %{iso_dir}/windows.iso

register_component
popd
#endregion
#region Other VMware Tools Images
%{__install} -Dm 644 %{SOURCE1} %{iso_dir}/linux.iso
%{__install} -Dm 644 %{SOURCE2} %{iso_dir}/linuxPreGlibc25.iso
%{__install} -Dm 644 %{SOURCE3} %{iso_dir}/netware.iso
%{__install} -Dm 644 %{SOURCE4} %{iso_dir}/solaris.iso
%{__install} -Dm 644 %{SOURCE5} %{iso_dir}/winPre2k.iso
%{__install} -Dm 644 %{SOURCE6} %{iso_dir}/winPreVista.iso
%{__install} -Dm 644 %{SOURCE7} %{iso_dir}/winVista.iso

for iso in \
	linux \
	linuxPreGlibc25 \
	netware \
	solaris \
	winPre2k \
	winPreVista \
	winVista
do
	sqlite3 %{installer_database} "INSERT INTO components(name,version,buildNumber,component_core_id,longName,description,type) \
		VALUES('vmware-tools-${iso}','1',%{build_number},1,'${iso}','${iso}',1);"
done

#endregion
#region VMware Workstation Other Components
pushd vmware-other-apps

cp -r lib/* %{buildroot}%{_exec_prefix}/lib/vmware/
mkdir -p %{buildroot}%{_datadir}
cp -r share/* %{buildroot}%{_datadir}/
## Licences
mkdir -p %{buildroot}%{_docdir}/vmware-player
cp -r doc/* %{buildroot}%{_docdir}/vmware-player/

for target in \
	vmware-setup-helper \
	vmware-mount \
	vmware-fuseUI \
	vmware-app-control \
	vmware-zenity
do
	ln -s appLoader %{buildroot}%{_exec_prefix}/lib/vmware/bin/$target
done

ln -s ../lib/vmware/bin/vmware-mount %{buildroot}%{_bindir}/vmware-mount
ln -s ../lib/vmware/bin/vmware-fuseUI %{buildroot}%{_bindir}/vmware-fuseUI
ln -s ../lib/vmware/bin/vmrest %{buildroot}%{_bindir}/vmrest

register_component
popd
#endregion
#region VMware OVF Tool component for Linux
pushd vmware-ovftool

mkdir -p %{buildroot}%{_exec_prefix}/lib/vmware-ovftool/

cp -r * %{buildroot}%{_exec_prefix}/lib/vmware-ovftool/
chmod 755 %{buildroot}%{_exec_prefix}/lib/vmware-ovftool/ovftool*
ln -s ../lib/vmware-ovftool/ovftool %{buildroot}%{_bindir}/ovftool

register_component

popd
#endregion
#region VMware Network Editor User Interface
pushd vmware-network-editor-ui

cp -r share/* %{buildroot}%{_datadir}/

ln -s appLoader %{buildroot}%{_exec_prefix}/lib/vmware/bin/vmware-netcfg
ln -s ../lib/vmware/bin/vmware-netcfg %{buildroot}%{_bindir}/vmware-netcfg

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

%{__install} -Dm 644 %{SOURCE9} %{buildroot}%{_sysconfdir}/vmware-vix/bootstrap

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
#region Install Kernel Modules
pushd patched
%{__install} -Dm 755 vmmon.o %{buildroot}%{_exec_prefix}/lib/modules/%{kernel}.%{_arch}/extra/vmmon.ko
%{__install} -Dm 755 vmnet.o %{buildroot}%{_exec_prefix}/lib/modules/%{kernel}.%{_arch}/extra/vmnet.ko
find %{buildroot}%{_exec_prefix}/lib/modules -type f -name *.ko -exec xz --compress --check=crc32 --lzma2=dict=1MiB {} \;

%{__install} -Dm 644 %{SOURCE22} %{buildroot}%{_exec_prefix}/lib/modules-load.d/vmware.conf
popd
#endregion
#region VMWare Networks Services
%{__install} -Dm 644 %{SOURCE13} %{buildroot}%{_exec_prefix}/lib/systemd/system/vmware-networks-configuration.service
%{__install} -Dm 644 %{SOURCE14} %{buildroot}%{_exec_prefix}/lib/systemd/system/vmware-networks.service
%{__install} -Dm 644 %{SOURCE16} %{buildroot}%{_exec_prefix}/lib/systemd/system/vmware-networks.path
#endregion
#region Enable macOS Guests
%if %{with unlocker}
	## Edit unlocker.py to operate on buildroot
	sed -i -e "s|%{_exec_prefix}/lib/vmware/|%{buildroot}%{_exec_prefix}/lib/vmware/|" %{SOURCE23}
	%{__python3} %{SOURCE23}
	%{SOURCE27} %{buildroot}%{_exec_prefix}/lib/vmware/roms/EFI32.ROM %{SOURCE24} -o %{buildroot}%{_exec_prefix}/lib/vmware/roms/EFI32.ROM
	%{SOURCE27} %{buildroot}%{_exec_prefix}/lib/vmware/roms/EFI64.ROM %{SOURCE24} -o %{buildroot}%{_exec_prefix}/lib/vmware/roms/EFI64.ROM
	%{SOURCE27} %{buildroot}%{_exec_prefix}/lib/vmware/roms/EFI20-32.ROM %{SOURCE24} -o %{buildroot}%{_exec_prefix}/lib/vmware/roms/EFI20-32.ROM
	%{SOURCE27} %{buildroot}%{_exec_prefix}/lib/vmware/roms/EFI20-64.ROM %{SOURCE24} -o %{buildroot}%{_exec_prefix}/lib/vmware/roms/EFI20-64.ROM
	%{__install} -Dm 644 %{SOURCE25} %{iso_dir}/darwin.iso
	%{__install} -Dm 644 %{SOURCE26} %{iso_dir}/darwinPre15.iso
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
for iso in \
	windows \
	linux \
	linuxPreGlibc25 \
	netware \
	solaris \
	winPre2k \
	winPreVista \
	winVista
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
for module in \
	vmmon \
	vmnet
do
	test -s %{buildroot}%{_exec_prefix}/lib/modules/%{kernel}.%{_arch}/extra/${module}.ko.xz
done

%post
[ $1 -eq 1 ] && semanage fcontext --add --type vmware_host_exec_t %{_exec_prefix}/lib/vmware/bin/vmware-usbarbitrator
restorecon %{_exec_prefix}/lib/vmware/bin/vmware-usbarbitrator

%postun
[ $1 -eq 0 ] && semanage fcontext --delete --type vmware_host_exec_t %{_exec_prefix}/lib/vmware/bin/vmware-usbarbitrator

%post -n kmod-vmware
if [ -f %{key} ] && [ -f %{cert} ]
then
	cd %{_exec_prefix}/lib/modules/%{kernel}.%{_arch}/extra
	find . -type f -regextype posix-extended -regex '.*vm(mon|net)\.ko\.xz' -exec xz --decompress {} \;
	find . -type f -regextype posix-extended -regex '.*vm(mon|net)\.ko' \
		-exec %{_usrsrc}/kernels/%{kernel}.%{_arch}/scripts/sign-file sha256 %{key} %{cert} {} \; \
		-exec xz --compress --check=crc32 --lzma2=dict=1MiB {} \;
else
	echo 'MOK not found, not signing vmmon.ko and vmnet.ko!'
	return 1
fi

%triggerin -n kmod-vmware -- kmod-vmware
mkdir -p %{_localstatedir}/lib/rpm-state/kmods
rpm -ql kmod-vmware-%{?epoch:%{epoch}:}%{version}-%{release}.%{_arch} | grep -E '%{_exec_prefix}/lib/modules/%{kernel}.%{_arch}/.*\.ko(\.gz|\.bz2|\.xz|\.zst)?$' >> %{_localstatedir}/lib/rpm-state/kmods/weak-modules

%triggerun -n kmod-vmware -- kmod-vmware
mkdir -p %{_localstatedir}/lib/rpm-state/kmods
rpm -ql kmod-vmware-%{?epoch:%{epoch}:}%{version}-%{release}.%{_arch} | grep -E '%{_exec_prefix}/lib/modules/%{kernel}.%{_arch}/.*\.ko(\.gz|\.bz2|\.xz|\.zst)?$' >> %{_localstatedir}/lib/rpm-state/kmods/weak-modules

%preun -n kmod-vmware
mkdir -p %{_localstatedir}/lib/rpm-state/kmods
rpm -ql kmod-vmware-%{?epoch:%{epoch}:}%{version}-%{release}.%{_arch} | grep -E '%{_exec_prefix}/lib/modules/%{kernel}.%{_arch}/.*\.ko(\.gz|\.bz2|\.xz|\.zst)?$' >> %{_localstatedir}/lib/rpm-state/kmods/weak-modules-remove

%define kmod_posttrans \
if [ -f %{_localstatedir}/lib/rpm-state/kmods/weak-modules ]\
then\
	while read -r MODULE\
	do\
		if [ -f "$MODULE" ]\
		then\
			printf '%s\\n' "$MODULE" >> %{_localstatedir}/lib/rpm-state/kmods/weak-modules-add\
		fi\
	done < %{_localstatedir}/lib/rpm-state/kmods/weak-modules\
	rm -f %{_localstatedir}/lib/rpm-state/kmods/weak-modules\
fi\
if [ -f %{_localstatedir}/lib/rpm-state/kmods/weak-modules-remove ]\
then\
	modules=( $(cat %{_localstatedir}/lib/rpm-state/kmods/weak-modules-remove | sort -u -V -t '/' -k 5 -k 4,4) )\
	rm -f %{_localstatedir}/lib/rpm-state/kmods/weak-modules-remove\
	if [ -f %{_localstatedir}/lib/rpm-state/kmods/weak-modules-add ]\
	then\
		printf '%s\\n' "${modules[@]}" | %{_sbindir}/weak-modules --remove-modules --no-initramfs\
	else\
		printf '%s\\n' "${modules[@]}" | %{_sbindir}/weak-modules --remove-modules\
	fi\
fi\
if [ -f %{_localstatedir}/lib/rpm-state/kmods/weak-modules-add ]\
then\
	modules=( $(cat %{_localstatedir}/lib/rpm-state/kmods/weak-modules-add | sort -u -V -t '/' -k 5 -k 4,4) )\
	rm -f %{_localstatedir}/lib/rpm-state/kmods/weak-modules-add\
	printf '%s\\n' "${modules[@]}" | %{_sbindir}/weak-modules --add-modules\
fi\
if [ -d %{_localstatedir}/lib/rpm-state/kmods ]\
then\
	rmdir --ignore-fail-on-non-empty %{_localstatedir}/lib/rpm-state/kmods\
fi\

%posttrans -n kmod-vmware %{kmod_posttrans}
%postuntrans -n kmod-vmware %{kmod_posttrans}

#region files
%files
%defattr(0644, root, root, 0755)
%{_sysconfdir}/modprobe.d/modprobe-vmware-fuse.conf
%{_sysconfdir}/vmware/
%{_sysconfdir}/vmware-installer/
%ghost %{_sysconfdir}/vmware-tools/
%{_sysconfdir}/vmware-vix/
%{_includedir}/vmware-vix/
%{_exec_prefix}/lib/systemd/system/vmware-networks-configuration.service
%{_exec_prefix}/lib/systemd/system/vmware-networks.path
%{_exec_prefix}/lib/systemd/system/vmware-networks.service
%{_exec_prefix}/lib/systemd/system/vmware-usbarbitrator.path
%{_exec_prefix}/lib/systemd/system/vmware-usbarbitrator.service
%{_exec_prefix}/lib/vmware/
%{_exec_prefix}/lib/vmware-installer/
%{_exec_prefix}/lib/vmware-ovftool/
%{_exec_prefix}/lib/vmware-vix/
%{_datadir}/appdata/vmware-workstation.appdata.xml
%{_datadir}/applications/vmware-netcfg.desktop
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
%{_exec_prefix}/lib/vmware/bin/mkisofs
%{_exec_prefix}/lib/vmware/bin/mksSandbox*
%{_exec_prefix}/lib/vmware/bin/tpm2emu*
%{_exec_prefix}/lib/vmware/bin/vmrest
%{_exec_prefix}/lib/vmware/bin/vmware
%{_exec_prefix}/lib/vmware/bin/vmware-app-control
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

%files -n kmod-vmware
%defattr(0644, root, root, 0755)
%verify(not md5 size mtime)%{_exec_prefix}/lib/modules/%{kernel}.%{_arch}/extra/vmmon.ko.xz
%verify(not md5 size mtime)%{_exec_prefix}/lib/modules/%{kernel}.%{_arch}/extra/vmnet.ko.xz
%{_exec_prefix}/lib/modules-load.d/vmware.conf

#endregion

%changelog
%autochangelog
