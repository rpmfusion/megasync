%global sdk_version 5.2.3
%global source_suffix OSX

%bcond_without dolphin
%if 0%{?fedora} > 36
%bcond_with nautilus
%else
%bcond_without nautilus
%endif
%if 0%{?rhel} == 8
%bcond_with nemo
%else
%bcond_without nemo
%endif

Name:       megasync
Version:    5.2.1.0
Release:    4%{?dist}
Summary:    Easy automated syncing between your computers and your MEGA cloud drive
# MEGAsync is under a proprietary license, except the SDK which is BSD
License:    Proprietary and BSD
URL:        https://mega.nz
Source0:    https://github.com/meganz/MEGAsync/archive/v%{version}_%{source_suffix}.tar.gz
Source1:    https://github.com/meganz/sdk/archive/v%{sdk_version}.tar.gz
Patch0:     ffmpeg6.patch

ExcludeArch:    %power64 %arm32 %arm64

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
BuildRequires:  libatomic
BuildRequires:  cryptopp-devel >= 5.6.5
BuildRequires:  desktop-file-utils
BuildRequires:  qt5-qtbase-devel >= 5.6
BuildRequires:  qt5-qttools-devel
BuildRequires:  qt5-qtsvg-devel
BuildRequires:  qt5-qtx11extras-devel
BuildRequires:  qt5-qtdeclarative-devel
BuildRequires:  terminus-fonts
BuildRequires:  fontpackages-filesystem
BuildRequires:  LibRaw-devel
BuildRequires:  libsodium-devel
BuildRequires:  libuv-devel
BuildRequires:  sqlite-devel
BuildRequires:  vcpkg
BuildRequires:  systemd-devel
BuildRequires:  freeimage-devel
BuildRequires:  fuse-devel

Requires:       hicolor-icon-theme

# Fedora now has a stripped ffmpeg. Make sure we're using the full version.
%if 0%{?fedora} && 0%{?fedora} >= 36
Requires: ffmpeg-libs%{?_isa}
%endif

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
%setup -q -n MEGAsync-%{version}_%{source_suffix}

#Move Mega SDK to it's place
tar -xvf %{SOURCE1} -C src/MEGASync/mega
mv src/MEGASync/mega/sdk-%{sdk_version}/* src/MEGASync/mega/
%patch 0 -p0
cp src/MEGASync/mega/LICENSE LICENSE-SDK

%if 0%{?fedora} >= 35
# Fix glibc for F35 and later
sed -i 's|kSigStackSize = std::max(8192|kSigStackSize = std::max(static_cast<long>(8192)|' src/MEGASync/google_breakpad/client/linux/handler/exception_handler.cc
%endif

#Disable all bundling
sed -i 's/-u/-f/' src/configure
sed -i 's/-v/-y/' src/configure
sed -i 's|disable_sqlite=0|disable_sqlite=1|' src/MEGASync/mega/contrib/build_sdk.sh

#Correct build for rawhide
sed -i 's|static int tgkill|int tgkill|' src/MEGASync/google_breakpad/client/linux/handler/exception_handler.cc

# Disable pdfium
sed -i '/DEFINES += REQUIRE_HAVE_PDFIUM/d' src/MEGASync/MEGASync.pro

# Fix build with new glibc
# https://github.com/meganz/MEGAsync/pull/477
sed -i 's|sys_siglist\[sig\]|strsignal(sig)|' src/MEGASync/control/CrashHandler.cpp

#Fix FFMPEG 5 sdk build
sed -i -e 's|AVCodec\* decoder|auto decoder|' src/MEGASync/mega/src/gfx/freeimage.cpp

#Fix Nemo plugin build
sed -i "s|void mega_ext_on_sync_del(MEGAExt \*mega_ext, const gchar \*path);|void mega_ext_on_sync_del(MEGAExt \*mega_ext, const gchar \*path);\nvoid expanselocalpath(char \*path, char \*absolutepath);|" src/MEGAShellExtNemo/MEGAShellExt.h
sed -i "s|#include <string.h>|#include <string.h>\n#include <stdio.h>|" src/MEGAShellExtNemo/mega_ext_client.c

%build
#Enable FFMPEG
echo "CONFIG += link_pkgconfig
PKGCONFIG += libavcodec" >> src/MEGASync/MEGASync.pro

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
pushd src/MEGAShellExtDolphin
    %cmake_kf5
    %cmake_build
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
pushd src/MEGAShellExtDolphin
    %cmake_install
popd
%endif

%if %{with nautilus}
sed -i 's|$(INSTALL_ROOT)/builddir|/builddir|' src/MEGAShellExtNautilus/build/Makefile
pushd src/MEGAShellExtNautilus/build
    %make_install INSTALL_ROOT=%{buildroot} DESKTOP_DESTDIR=%{_prefix}
    mkdir -p %{buildroot}%{_libdir}/nautilus/extensions-3.0
    install -pm 755 libMEGAShellExtNautilus.so \
        %{buildroot}%{_libdir}/nautilus/extensions-3.0/libMEGAShellExtNautilus.so
    rm %{buildroot}%{_datadir}/icons/hicolor/icon-theme.cache
popd
%endif

%if %{with nemo}
sed -i 's|$(INSTALL_ROOT)/builddir|/builddir|' src/MEGAShellExtNemo/build/Makefile
pushd src/MEGAShellExtNemo/build
    %make_install INSTALL_ROOT=%{buildroot} DESKTOP_DESTDIR=%{_prefix}
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
%{_libdir}/nautilus/extensions-3.0/libMEGAShellExtNautilus.so*
%exclude %{_datadir}/icons/hicolor/*/emblems/mega-dolphin-*.png
%exclude %{_datadir}/icons/hicolor/*/emblems/mega-nemo*.png
%{_datadir}/icons/hicolor/*/*/mega-*.icon
%{_datadir}/icons/hicolor/*/*/mega-*.png
%endif

%if %{with nemo}
%files -n nemo-%{name}
%{_libdir}/nemo/extensions-3.0/libMEGAShellExtNemo.so*
%{_datadir}/icons/hicolor/*/*/mega-nemo*.icon
%{_datadir}/icons/hicolor/*/*/mega-nemo*.png
%endif

%changelog
* Wed Jan 29 2025 RPM Fusion Release Engineering <sergiomb@rpmfusion.org> - 5.2.1.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_42_Mass_Rebuild

* Sat Oct 12 2024 Vasiliy Glazov <vascom2@gmail.com> - 5.2.1.0-3
- Rebuild for new ffmpeg

* Sat Aug 03 2024 RPM Fusion Release Engineering <sergiomb@rpmfusion.org> - 5.2.1.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_41_Mass_Rebuild

* Thu Jun 20 2024 Vasiliy Glazov <vascom2@gmail.com> - 5.2.1.0-1
- Update to 5.2.1.0

* Tue Mar 19 2024 Vasiliy Glazov <vascom2@gmail.com> - 5.2.0.0-1
- Update to 5.2.0.0

* Sun Feb 04 2024 RPM Fusion Release Engineering <sergiomb@rpmfusion.org> - 4.12.2.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_40_Mass_Rebuild

* Fri Jan 26 2024 Vasiliy Glazov <vascom2@gmail.com> - 4.12.2.0-1
- Update to 4.12.2.0

* Thu Jan 25 2024 Vasiliy Glazov <vascom2@gmail.com> - 4.12.1.0-1
- Update to 4.12.1.0

* Mon Dec 04 2023 Vasiliy Glazov <vascom2@gmail.com> - 4.11.0.0-1
- Update to 4.11.0.0

* Thu Oct 19 2023 Vasiliy Glazov <vascom2@gmail.com> - 4.10.0.0-1
- Update to 4.10.0.0

* Fri Aug 04 2023 Vasiliy Glazov <vascom2@gmail.com> - 4.9.6.0-1
- Update to 4.9.6.0

* Thu Aug 03 2023 RPM Fusion Release Engineering <sergiomb@rpmfusion.org> - 4.9.5.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_39_Mass_Rebuild

* Fri Jun 30 2023 Vasiliy Glazov <vascom2@gmail.com> - 4.9.5.0-1
- Update to 4.9.5.0

* Tue May 23 2023 Vasiliy Glazov <vascom2@gmail.com> - 4.9.4.0-1
- Update to 4.9.4.0

* Sun Apr 02 2023 Vasiliy Glazov <vascom2@gmail.com> - 4.9.1.0-1
- Update to 4.9.1.0

* Mon Mar 13 2023 Leigh Scott <leigh123linux@gmail.com> - 4.9.0.0-2
- rebuilt

* Mon Mar 06 2023 Vasiliy Glazov <vascom2@gmail.com> - 4.9.0.0-1
- Update to 4.9.0.0

* Tue Feb 28 2023 Vasiliy Glazov <vascom2@gmail.com> - 4.8.8.0-1
- Update to 4.8.8.0

* Sat Feb 04 2023 Vasiliy Glazov <vascom2@gmail.com> - 4.8.7.0-1
- Update to 4.8.7.0

* Fri Jan 27 2023 Vasiliy Glazov <vascom2@gmail.com> - 4.8.6.0-1
- Update to 4.8.6.0

* Tue Dec 13 2022 Vasiliy Glazov <vascom2@gmail.com> - 4.7.3.0-2
- Update sources

* Fri Nov 18 2022 Vasiliy Glazov <vascom2@gmail.com> - 4.7.3.0-1
- Update to 4.7.3.0

* Mon Nov 14 2022 Vasiliy Glazov <vascom2@gmail.com> - 4.7.2.0-1
- Update to 4.7.2.0

* Tue Oct 04 2022 Vasiliy Glazov <vascom2@gmail.com> - 4.7.1.0-1
- Update to 4.7.1.0

* Mon Sep 26 2022 Vasiliy Glazov <vascom2@gmail.com> - 4.7.0.0-1
- Update to 4.7.0.0

* Mon Aug 08 2022 RPM Fusion Release Engineering <sergiomb@rpmfusion.org> - 4.6.7.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_37_Mass_Rebuild and ffmpeg
  5.1

* Mon Jun 27 2022 Vasiliy Glazov <vascom2@gmail.com> - 4.6.7.0-1
- Update to 4.6.7.0

* Tue Apr 12 2022 Vasiliy N. Glazov <vascom2@gmail.com> - 4.6.6.0-2
- Disable armv7 build

* Mon Apr 11 2022 Vasiliy N. Glazov <vascom2@gmail.com> - 4.6.6.0-1
- Update to 4.6.6.0

* Mon Apr 04 2022 Vasiliy N. Glazov <vascom2@gmail.com> - 4.6.5.0-3
- Fix build with ffmpeg 5
- Require full ffmpeg libs

* Wed Mar 30 2022 Vasiliy N. Glazov <vascom2@gmail.com> - 4.6.5.0-1
- Update to 4.6.5.0

* Thu Feb 10 2022 RPM Fusion Release Engineering <sergiomb@rpmfusion.org> - 4.6.3.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_36_Mass_Rebuild

* Sat Jan 29 2022 Vasiliy N. Glazov <vascom2@gmail.com> - 4.6.3.0-1
- Update to 4.6.3.0

* Thu Jan 27 2022 Vasiliy N. Glazov <vascom2@gmail.com> - 4.5.3.0-3
-  Rebuild without LTO

* Tue Sep 28 2021 Vasiliy N. Glazov <vascom2@gmail.com> - 4.5.3.0-2
-  Rebuild for new cryptopp

* Fri Sep 17 2021 Vasiliy N. Glazov <vascom2@gmail.com> - 4.5.3.0-1
- Update to 4.5.3.0
- Fix ffmeg

* Wed Aug 04 2021 RPM Fusion Release Engineering <leigh123linux@gmail.com> - 4.4.0.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_35_Mass_Rebuild

* Mon Mar 01 2021 Vasiliy N. Glazov <vascom2@gmail.com> - 4.4.0.0-1
- Update to 4.4.0.0

* Thu Feb 04 2021 RPM Fusion Release Engineering <leigh123linux@gmail.com> - 4.3.7.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_34_Mass_Rebuild

* Fri Jan 01 2021 Vasiliy N. Glazov <vascom2@gmail.com> - 4.3.7.0-2
- Rebuilt for new cryptopp

* Mon Nov 23 2020 Vasiliy N. Glazov <vascom2@gmail.com> - 4.3.7.0-1
- Update to 4.3.7.0

* Wed Nov 11 2020 Vasiliy N. Glazov <vascom2@gmail.com> - 4.3.5.0-1
- Update to 4.3.5.0

* Wed Aug 19 2020 RPM Fusion Release Engineering <leigh123linux@gmail.com> - 4.3.3.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Mon Jul 27 2020 Vasiliy N. Glazov <vascom2@gmail.com> - 4.3.3.0-1
- Update to 4.3.3.0

* Sun May 24 2020 Leigh Scott <leigh123linux@gmail.com> - 4.3.1.0-2
- Rebuild for new libraw version

* Thu Mar 26 2020 Vasiliy N. Glazov <vascom2@gmail.com> - 4.3.1.0-1
- Update to 4.3.1.0

* Wed Mar 04 2020 Vasiliy N. Glazov <vascom2@gmail.com> - 4.3.0.8-1
- Update to 4.3.0.8

* Wed Feb 05 2020 RPM Fusion Release Engineering <leigh123linux@gmail.com> - 4.2.5-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Wed Sep 18 2019 Vasiliy N. Glazov <vascom2@gmail.com> - 4.2.5-1
- Update to 4.2.5

* Fri Aug 23 2019 Vasiliy N. Glazov <vascom2@gmail.com> - 4.2.3-1
- Update to 4.2.3

* Wed Aug 07 2019 Leigh Scott <leigh123linux@gmail.com> - 4.1.1-2
- Rebuild for new ffmpeg version

* Fri Jun 14 2019 Vasiliy N. Glazov <vascom2@gmail.com> - 4.1.1-1
- Update to 4.1.1

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
