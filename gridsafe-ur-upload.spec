%define py27 /usr/bin/python27

Name:           gridsafe-ur-upload
Version:        0.1
Release:        3%{?dist}.srce
Summary:        Package provides scripts for generating and uploading usage records to Gridsafe Accounting Web Service
License:        GPL
Vendor:         SRCE 
Source0:        gridsafe-ur-upload-%{version}.tar.gz
BuildArch:      noarch
Requires:       python(abi) >= 2.7
Requires:       gridsafe-ige-client
Requires:       gridsafe-ige-batch2ur-scripts 

%description
Package provides scripts for generating and uploading usage records to Gridsafe
Accounting Web Service. It is a bridge between batch2ur utility that generates
usage records from Globus and SGE accounting files/DB and gridsafe-ige-client
that uploads them to Web Service.

%prep
%setup -q

%build
%{py27} setup.py build

%install
rm -rf $RPM_BUILD_ROOT
%{py27} setup.py install -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%attr(0644,root,root) %{_sysconfdir}/cron.d/gridsafe-ur-upload
%config(noreplace) %{_sysconfdir}/%{name}/gridsafe-ur-upload.ini

%changelog
* Wed Sep 30 2015 Daniel Vrcic <dvrcic@srce.hr> - 0.1-3%{?dist}
- look for job end time instead of submission time
* Fri Aug 28 2015 Daniel Vrcic <dvrcic@srce.hr> - 0.1-2%{?dist}
- added configuration file
* Thu Aug 27 2015 Daniel Vrcic <dvrcic@srce.hr> - 0.1-1%{?dist}
- initial version
