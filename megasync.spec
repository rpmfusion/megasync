%global sdk_version 10.8.2
%global source_suffix Linux

%bcond_without dolphin
%bcond_without nautilus
%if 0%{?rhel} == 8
%bcond_with nemo
%else
%bcond_without nemo
%endif

Name:       megasync
Version:    6.2.2.0
Release:    1%{?dist}
Summary:    Easy automated syncing between your computers and your MEGA cloud drive
# MEGAsync is under a proprietary license, except the SDK which is BSD
License:    Proprietary and BSD
URL:        https://mega.nz
Source0:    https://github.com/meganz/MEGAsync/archive/v%{version}_%{source_suffix}/MEGAsync-%{version}_%{source_suffix}.tar.gz
Source1:    https://github.com/meganz/sdk/archive/v%{sdk_version}/sdk-%{sdk_version}.tar.gz
Patch0:     megasync-link-zlib.patch
Patch1:     010-megasync-sdk-fix-cmake-dependencies-detection.patch
Patch2:     020-megasync-app-fix-cmake-dependencies-detection.patch
Patch3:     040-megasync-sdk-add-missing-icu-link-library.patch

ExcludeArch:    %power64 %arm32 %arm64

BuildRequires:  openssl-devel
BuildRequires:  sqlite-devel
BuildRequires:  zlib-devel
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
BuildRequires:  readline-devel
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
BuildRequires:  pkgconfig(libnautilus-extension-4) 
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
%patch 0 -p1
%patch 1 -p1 -d src/MEGASync/mega
%patch 2 -p1
%patch 3 -p1 -d src/MEGASync/mega
cp src/MEGASync/mega/LICENSE LICENSE-SDK

#Network needed to download this pointless unused file
sed -i '/include(get_clang_format)/d; /get_clang_format()/d' CMakeLists.txt

#Fix Nemo plugin build
sed -i 's/^void expanselocalpath(char \*path, char \*absolutepath);//' src/MEGAShellExtNemo/MEGAShellExt.h

#Help it find freeimage
sed -i 's/.*find_package.*[Ff]ree[Ii]mage.*/# bypassed/' src/MEGASync/mega/cmake/modules/sdklib_libraries.cmake
sed -i 's/FreeImage::FreeImage/${FreeImage_LIBRARY}/g' src/MEGASync/mega/cmake/modules/sdklib_libraries.cmake

%build
%cmake \
 -DCMAKE_BUILD_TYPE=Release \
 -DCMAKE_MODULE_PATH:PATH="src/MEGASync/mega/cmake/modules/packages" \
 -DCMAKE_SKIP_INSTALL_RPATH:BOOL='YES' \
 -DENABLE_DESIGN_TOKENS_IMPORTER:BOOL='OFF' \
 -DENABLE_DESKTOP_APP_TESTS:BOOL='OFF' \
 -DUSE_BREAKPAD:BOOL='OFF' \
 -DUSE_FFMPEG:BOOL='ON' \
 -DUSE_FREEIMAGE:BOOL=ON \
 -DUSE_PDFIUM:BOOL='OFF' \
 -DCMAKE_INSTALL_PREFIX=/ \
 -DCMAKE_SHARED_LINKER_FLAGS="-lfreeimage" \
 -DCMAKE_EXE_LINKER_FLAGS="-Wl,--no-as-needed -lz -lfreeimage" \
 -Wno-dev

%cmake_build

%if %{with dolphin}
pushd src/MEGAShellExtDolphin
    %cmake_kf5
    %cmake_build
popd
%endif

%if %{with nautilus}
pushd src/MEGAShellExtNautilus
    %cmake
    %cmake_build
popd
%endif

%if %{with nemo}
pushd src/MEGAShellExtNemo
    %cmake
    %cmake_build
popd
%endif

%install
%cmake_install

desktop-file-install \
 --add-category="Network" \
 --dir %{buildroot}%{_datadir}/applications \
%{buildroot}%{_datadir}/applications/%{name}.desktop

#Remove ubuntu specific themes
rm -rf %{buildroot}%{_datadir}/icons/ubuntu*

#Remove /opt directory
rm -r %{buildroot}/opt

%if %{with dolphin}
pushd src/MEGAShellExtDolphin
    %cmake_install
popd
%endif

%if %{with nautilus}
pushd src/MEGAShellExtNautilus
    %cmake_install
popd
%endif

%if %{with nemo}
pushd src/MEGAShellExtNemo
    %cmake_install
popd
%endif

%files
%license LICENCE.md LICENSE-SDK
%{_bindir}/%{name}
%{_bindir}/mega-desktop-app-gfxworker
%{_datadir}/applications/%{name}.desktop
%{_datadir}/icons/hicolor/*/apps/mega.png
%{_datadir}/icons/hicolor/scalable/status/*.svg
%{_datadir}/%{name}/

%if %{with dolphin}
%files -n dolphin-%{name}
%{_kf5_plugindir}/overlayicon/
%{_kf5_plugindir}/kfileitemaction/
%{_datadir}/icons/hicolor/*/emblems/mega-dolphin-*.png
%endif

%if %{with nautilus}
%files -n nautilus-%{name}
%{_libdir}/nautilus/extensions-4/libMEGAShellExtNautilus.so*
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
* Wed Apr 22 2026 Leigh Scott <leigh123linux@gmail.com> - 6.2.2.0-1
- Update to 6.2.2.0

* Mon Feb 02 2026 RPM Fusion Release Engineering <sergiomb@rpmfusion.org> - 5.2.1.0-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_44_Mass_Rebuild

* Wed Nov 05 2025 Leigh Scott <leigh123linux@gmail.com> - 5.2.1.0-6
- Rebuild for ffmpeg-8.0

* Sun Jul 27 2025 RPM Fusion Release Engineering <sergiomb@rpmfusion.org> - 5.2.1.0-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_43_Mass_Rebuild

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
