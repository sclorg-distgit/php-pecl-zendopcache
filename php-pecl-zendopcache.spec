# spec file for php-pecl-zendopcache
#
# Copyright (c) 2013-2015 Remi Collet
# License: CC-BY-SA
# http://creativecommons.org/licenses/by-sa/3.0/
#
# Please, preserve the changelog entries
#
%{?scl: %scl_package php-pecl-zendopcache}
%{!?scl:        %global pkg_name   %{name}}
%{!?php_inidir: %global php_inidir %{_sysconfdir}/php.d}
%{!?__php:      %global __php      %{_bindir}/php}
%{!?__pecl:     %global __pecl     %{_bindir}/pecl}
%global with_zts   0%{?__ztsphp:1}
%global proj_name  ZendOpcache
%global pecl_name  zendopcache
%global plug_name  opcache

Name:          %{?scl_prefix}php-pecl-%{pecl_name}
Version:       7.0.4
Release:       3%{?dist}
Summary:       The Zend OPcache

Group:         Development/Libraries
License:       PHP
URL:           http://pecl.php.net/package/%{proj_name}
Source0:       http://pecl.php.net/get/%{pecl_name}-%{version}.tgz
# this extension must be loaded before XDebug
# So "opcache" if before "xdebug"
Source1:       %{plug_name}.ini
Source2:       %{plug_name}-default.blacklist

# Upstream patches
Patch0:        %{plug_name}-tests.patch
Patch1:        %{plug_name}-CVE-2015-1352.patch

BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires: %{?scl_prefix}php-devel >= 5.2.0
BuildRequires: %{?scl_prefix}php-pear

Requires(post): %{__pecl}
Requires(postun): %{__pecl}
Requires:      %{?scl_prefix}php(zend-abi) = %{php_zend_api}
Requires:      %{?scl_prefix}php(api) = %{php_core_api}

# Only one opcode cache could be enabled
Conflicts:     %{?scl_prefix}php-eaccelerator
Conflicts:     %{?scl_prefix}php-xcache
# APC 3.1.15 offer an option to disable opcache
Conflicts:     %{?scl_prefix}php-pecl-apc < 3.1.15
Provides:      %{?scl_prefix}php-pecl(%{plug_name}) = %{version}%{?prever}
Provides:      %{?scl_prefix}php-pecl(%{plug_name})%{?_isa} = %{version}%{?prever}
Provides:      %{?scl_prefix}php-%{plug_name} = %{version}-%{release}
Provides:      %{?scl_prefix}php-%{plug_name}%{?_isa} = %{version}-%{release}

# Filter private shared
%{?filter_provides_in: %filter_provides_in %{_libdir}/.*\.so$}
%{?filter_setup}


%description
The Zend OPcache provides faster PHP execution through opcode caching and
optimization. It improves PHP performance by storing precompiled script
bytecode in the shared memory. This eliminates the stages of reading code from
the disk and compiling it on future access. In addition, it applies a few
bytecode optimization patterns that make code execution faster.


%prep
%setup -q -c
mv %{pecl_name}-%{version} NTS

cd NTS
%patch0 -p1 -b .upstream
%patch1 -p1 -b .cve1351

# Sanity check, really often broken
extver=$(sed -n '/#define PHP_ZENDOPCACHE_VERSION/{s/.* "//;s/".*$//;p}' ZendAccelerator.h)
if test "x${extver}" != "x%{version}%{?prever:-%{prever}}"; then
   : Error: Upstream extension version is ${extver}, expecting %{version}%{?prever:-%{prever}}.
   exit 1
fi
cd ..

%if %{with_zts}
# Duplicate source tree for NTS / ZTS build
cp -pr NTS ZTS
%endif


%build
cd NTS
%{_bindir}/phpize
%configure \
    --enable-opcache \
    --with-php-config=%{_bindir}/php-config
make %{?_smp_mflags}

%if %{with_zts}
cd ../ZTS
%{_bindir}/zts-phpize
%configure \
    --enable-opcache \
    --with-php-config=%{_bindir}/zts-php-config
make %{?_smp_mflags}
%endif


%install
rm -rf %{buildroot}

make -C NTS install INSTALL_ROOT=%{buildroot}

# Configuration file
install -D -p -m 644 %{SOURCE1} %{buildroot}%{php_inidir}/%{plug_name}.ini
sed -e 's:@EXTPATH@:%{php_extdir}:' \
    -e 's:@INIPATH@:%{php_inidir}:' \
    -i %{buildroot}%{php_inidir}/%{plug_name}.ini

# The default Zend OPcache blacklist file
install -D -p -m 644 %{SOURCE2} %{buildroot}%{php_inidir}/%{plug_name}-default.blacklist

%if %{with_zts}
make -C ZTS install INSTALL_ROOT=%{buildroot}

install -D -p -m 644 %{SOURCE1} %{buildroot}%{php_ztsinidir}/%{plug_name}.ini
sed -e 's:@EXTPATH@:%{php_ztsextdir}:' \
    -e 's:@INIPATH@:%{php_ztsinidir}:' \
    -i %{buildroot}%{php_ztsinidir}/%{plug_name}.ini

install -D -p -m 644 %{SOURCE2} %{buildroot}%{php_ztsinidir}/%{plug_name}-default.blacklist
%endif

# Install XML package description
install -D -m 644 package.xml %{buildroot}%{pecl_xmldir}/%{name}.xml


%check
cd NTS
%{__php} \
    -n -d zend_extension=%{buildroot}%{php_extdir}/%{plug_name}.so \
    -m | grep "Zend OPcache"

TEST_PHP_EXECUTABLE=%{__php} \
TEST_PHP_ARGS="-n -d zend_extension=%{buildroot}%{php_extdir}/%{plug_name}.so" \
NO_INTERACTION=1 \
REPORT_EXIT_STATUS=1 \
%{__php} -n run-tests.php

%if %{with_zts}
cd ../ZTS
%{__ztsphp} \
    -n -d zend_extension=%{buildroot}%{php_ztsextdir}/%{plug_name}.so \
    -m | grep "Zend OPcache"

TEST_PHP_EXECUTABLE=%{__ztsphp} \
TEST_PHP_ARGS="-n -d zend_extension=%{buildroot}%{php_ztsextdir}/%{plug_name}.so" \
NO_INTERACTION=1 \
REPORT_EXIT_STATUS=1 \
%{__ztsphp} -n run-tests.php
%endif


%clean
rm -rf %{buildroot}


%post
%{pecl_install} %{pecl_xmldir}/%{name}.xml >/dev/null || :


%postun
if [ $1 -eq 0 ] ; then
    %{pecl_uninstall} %{pecl_name} >/dev/null || :
fi


%files
%defattr(-,root,root,-)
%doc NTS/{LICENSE,README}
%config(noreplace) %{php_inidir}/%{plug_name}-default.blacklist
%config(noreplace) %{php_inidir}/%{plug_name}.ini
%{php_extdir}/%{plug_name}.so

%if %{with_zts}
%config(noreplace) %{php_ztsinidir}/%{plug_name}-default.blacklist
%config(noreplace) %{php_ztsinidir}/%{plug_name}.ini
%{php_ztsextdir}/%{plug_name}.so
%endif

%{pecl_xmldir}/%{name}.xml


%changelog
* Wed Apr  8 2015 Remi Collet <rcollet@redhat.com> - 7.0.4-3
- fix use after free CVE-2015-1351

* Wed Jan 21 2015 Remi Collet <rcollet@redhat.com> - 7.0.4-2
- add upstream patch for failed test

* Mon Jan 12 2015 Remi Collet <rcollet@redhat.com> - 7.0.4-1
- Update to 7.0.4

* Thu Jan  8 2015 Remi Collet <rcollet@redhat.com> - 7.0.3-1
- update to 7.0.3 #1055927

* Tue Nov 19 2013 Remi Collet <rcollet@redhat.com> - 7.0.2-4
- rebuild for RHSCL 1.1

* Thu Jul 18 2013 Remi Collet <rcollet@redhat.com> - 7.0.2-3
- rebuild for new value of php(zend-abi) and php(api)

* Mon Jul 15 2013 Remi Collet <rcollet@redhat.com> - 7.0.2-2
- fix ZTS configuration
- Adapt for SCL

* Wed Jun  5 2013 Remi Collet <rcollet@redhat.com> - 7.0.2-1
- update to 7.0.2
- add spec License = CC-BY-SA

* Thu Apr 11 2013 Remi Collet <rcollet@redhat.com> - 7.0.1-2
- allow wildcard in opcache.blacklist_filename and provide
  default /etc/php.d/opcache-default.blacklist

* Mon Mar 25 2013 Remi Collet <remi@fedoraproject.org> - 7.0.1-1
- official PECL release, version 7.0.1 (beta)
- rename to php-pecl-zendopcache

* Mon Mar 18 2013 Remi Collet <remi@fedoraproject.org> - 7.0.1-0.1.gitcef6093
- update to git snapshot, with new name (opcache)

* Sun Mar 10 2013 Remi Collet <remi@fedoraproject.org> - 7.0.0-2
- allow to install with APC >= 3.1.15 (user data cache)

* Tue Mar  5 2013 Remi Collet <remi@fedoraproject.org> - 7.0.0-1
- official PECL release, version 7.0.0 (beta)

* Thu Feb 28 2013 Remi Collet <remi@fedoraproject.org> - 7.0.0-0.7.gitd39a49a
- new snapshot
- run test suite during build

* Thu Feb 21 2013 Remi Collet <remi@fedoraproject.org> - 7.0.0-0.6.git3a06991
- new snapshot

* Fri Feb 15 2013 Remi Collet <remi@fedoraproject.org> - 7.0.0-0.4.git2b6eede
- new snapshot (ZTS fixes)

* Thu Feb 14 2013 Remi Collet <remi@fedoraproject.org> - 7.0.0-0.3.gita84b588
- make zts build optional

* Thu Feb 14 2013 Remi Collet <remi@fedoraproject.org> - 7.0.0-0.2.gitafb43f5
- new snapshot
- better default configuration file (new upstream recommendation)
- License file now provided by upstream

* Wed Feb 13 2013 Remi Collet <remi@fedoraproject.org> - 7.0.0-0.1.gitaafc145
- initial package
