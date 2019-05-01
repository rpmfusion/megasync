%global sdk_version 3.4.7

%bcond_without dolphin
%bcond_without nautilus
%bcond_without nemo

%global enable_lto 1

Name:       megasync
Version:    4.0.2
Release:    3%{?dist}
Summary:    Easy automated syncing between your computers and your MEGA cloud drive
# MEGAsync is under a proprietary license, except the SDK which is BSD
License:    Proprietary and BSD
URL:        https://mega.nz
Source0:    https://github.com/meganz/MEGAsync/archive/v%{version}.0_Linux.tar.gz
Source1:    https://github.com/meganz/sdk/archive/v%{sdk_version}.tar.gz

ExcludeArch:    %power64 aarch64

BuildRequires:  openssl-devel
BuildRequires:  sqlite-devel
BuildRequires:  zlib-devel
BuildRequires:  automake
BuildRequires:  libtool
BuildRequires:  gcc-c++
BuildRequires:  wget
BuildRequires:  ffmpeg-devel
BuildRequires:  bzip2-devel
BuildRequires:  libmediainfo-devel
BuildRequires:  c-ares-devel
BuildRequires:  cryptopp-devel >= 5.6.5
BuildRequires:  desktop-file-utils
BuildRequires:  qt5-qtbase-devel >= 5.6
BuildRequires:  qt5-qttools-devel
BuildRequires:  qt5-qtsvg-devel
BuildRequires:  terminus-fonts
BuildRequires:  fontpackages-filesystem
BuildRequires:  LibRaw-devel
BuildRequires:  libsodium-devel
BuildRequires:  libuv-devel
BuildRequires:  sqlite-devel

Requires:       hicolor-icon-theme

%description
Secure:
Your data is encrypted end to end. Nobody can intercept it while in storage or
in transit.

Flexible:
Sync any folder from your PC to any folder in the cloud. Sync any number of
folders in parallel.

Fast:
Take advantage of MEGA's high-powered infrastructure and multi-connection
transfers.

Generous:
Store up to 50 GB for free!

%if %{with dolphin}
%package -n dolphin-%{name}
Summary:        Extension for Dolphin to interact with Megasync
BuildRequires:  cmake(KF5CoreAddons)
BuildRequires:  cmake(KF5KIO)
BuildRequires:  kf5-rpm-macros
BuildRequires:  extra-cmake-modules
Requires:       %{name}%{?_isa}

%description -n dolphin-%{name}
%{summary}.
%endif

%if %{with nautilus}
%package -n nautilus-%{name}
Summary:        Extension for Nautilus to interact with Megasync
BuildRequires:  pkgconfig(libnautilus-extension) >= 2.16.0
Requires:       nautilus%{?_isa}
Requires:       %{name}%{?_isa}

%description -n nautilus-%{name}
%{summary}.
%endif

%if %{with nemo}
%package -n nemo-%{name}
Summary:        Extension for Nemo to interact with Megasync
BuildRequires:  pkgconfig(libnemo-extension)
Requires:       nemo%{?_isa}
Requires:       %{name}%{?_isa}

%description -n nemo-%{name}
%{summary}.
%endif


%prep
%autosetup -n MEGAsync-%{version}.0_Linux

#Move Mega SDK to it's place
tar -xvf %{SOURCE1} -C src/MEGASync/mega
mv src/MEGASync/mega/sdk-%{sdk_version}/* src/MEGASync/mega/
cp src/MEGASync/mega/LICENSE LICENSE-SDK

#Disable all bundling
sed -i '/-u/d' src/configure
sed -i 's/-v/-y/' src/configure
sed -i '/qlite_pkg $build_dir $install_dir/d' src/MEGASync/mega/contrib/build_sdk.sh


%build
#Enable FFMPEG
echo "CONFIG += link_pkgconfig
PKGCONFIG += libavcodec" >> src/MEGASync/MEGASync.pro
#Enable LTO optimisation
%if %{enable_lto}
echo "QMAKE_CXXFLAGS += -flto
QMAKE_LFLAGS_RELEASE += -flto" >> src/MEGASync/MEGASync.pro
%endif

export DESKTOP_DESTDIR=%{buildroot}%{_prefix}

pushd src
    ./configure -i -z

    %qmake_qt5 \
        "CONFIG += FULLREQUIREMENTS" \
        DESTDIR=%{buildroot}%{_bindir} \
        THE_RPM_BUILD_ROOT=%{buildroot}
    lrelease-qt5 MEGASync/MEGASync.pro

    %make_build
popd

%if %{with dolphin}
mkdir src/MEGAShellExtDolphin/build
pushd src/MEGAShellExtDolphin/build
    rm ../megasync-plugin.moc
    mv ../CMakeLists_kde5.txt ../CMakeLists.txt
    %cmake_kf5 ..
    %make_build
popd
%endif

%if %{with nautilus}
mkdir src/MEGAShellExtNautilus/build
pushd src/MEGAShellExtNautilus/build
    %qmake_qt5 ..
    %make_build
popd
%endif

%if %{with nemo}
mkdir src/MEGAShellExtNemo/build
pushd src/MEGAShellExtNemo/build
    %qmake_qt5 ..
    %make_build
popd
%endif

%install
pushd src
    %make_install DESTDIR=%{buildroot}%{_bindir}

    desktop-file-install \
        --add-category="Network" \
        --dir %{buildroot}%{_datadir}/applications \
    %{buildroot}%{_datadir}/applications/%{name}.desktop

    #Remove ubuntu specific themes
    rm -rf %{buildroot}%{_datadir}/icons/ubuntu*
popd

%if %{with dolphin}
pushd src/MEGAShellExtDolphin/build
    %make_install
popd
%endif

%if %{with nautilus}
pushd src/MEGAShellExtNautilus/build
    %make_install
    mkdir -p %{buildroot}%{_libdir}/nautilus/extensions-3.0
    install -pm 755 libMEGAShellExtNautilus.so \
        %{buildroot}%{_libdir}/nautilus/extensions-3.0/libMEGAShellExtNautilus.so
    rm %{buildroot}%{_datadir}/icons/hicolor/icon-theme.cache
popd
%endif

%if %{with nemo}
pushd src/MEGAShellExtNemo/build
    %make_install
    mkdir -p %{buildroot}%{_libdir}/nemo/extensions-3.0
    install -pm 755 libMEGAShellExtNemo.so \
        %{buildroot}%{_libdir}/nemo/extensions-3.0/libMEGAShellExtNemo.so
    rm %{buildroot}%{_datadir}/icons/hicolor/icon-theme.cache
popd
%endif

%files
%license LICENCE.md LICENSE-SDK
%{_bindir}/%{name}
%{_datadir}/applications/%{name}.desktop
%{_datadir}/icons/hicolor/*/apps/mega.png
%{_datadir}/icons/hicolor/scalable/status/*.svg
%{_datadir}/doc/%{name}

%if %{with dolphin}
%files -n dolphin-%{name}
%{_kf5_plugindir}/overlayicon
%{_qt5_plugindir}/megasyncplugin.so
%{_datadir}/icons/hicolor/*/emblems/mega-dolphin-*.png
%{_datadir}/kservices5/%{name}-plugin.desktop
%endif

%if %{with nautilus}
%files -n nautilus-%{name}
%{_libdir}/nautilus/extensions-3.0/libMEGAShellExtNautilus.so
%exclude %{_datadir}/icons/hicolor/*/emblems/mega-dolphin-*.png
%exclude %{_datadir}/icons/hicolor/*/emblems/mega-nemo*.png
%{_datadir}/icons/hicolor/*/*/mega-*.icon
%{_datadir}/icons/hicolor/*/*/mega-*.png
%endif

%if %{with nemo}
%files -n nemo-%{name}
%{_libdir}/nemo/extensions-3.0/libMEGAShellExtNemo.so
%{_datadir}/icons/hicolor/*/*/mega-nemo*.icon
%{_datadir}/icons/hicolor/*/*/mega-nemo*.png
%endif

%changelog
* Tue Apr 23 2019 Vasiliy N. Glazov <vascom2@gmail.com> - 4.0.2-3
- Corrected license
- Added file manager plugins

* Mon Apr 22 2019 Vasiliy N. Glazov <vascom2@gmail.com> - 4.0.2-2
- Correct spec
- Add license files

* Fri Apr 19 2019 Vasiliy N. Glazov <vascom2@gmail.com> - 4.0.2-1
- Clean spec for fedora

* Mon Feb  4 2019 linux@mega.co.nz
- Update to version 4.0.2:
  * Fix bug with selection of transfer manager items
  * Fix bug of context menu not shown over transfer manager items
  * New design for the main dialog
  * Improved setup assistant
  * Support to show Public Service Announcements
  * Modern notifications
  * Updated third-party libraries
  * Other minor bug fixes and improvements
