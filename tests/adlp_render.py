#!/usr/bin/env python3
"""Run production profile selection: ADL-P Render must preserve Display13."""
from pathlib import Path
import re, subprocess, tempfile
r=Path(__file__).resolve().parents[1]
s=(r/'WhateverXe/kern_xe.cpp').read_text()
f=re.search(r'void XE::selectProfile\(.*?\n\}',s,re.S).group()
code=r'''
#include "kern_xelp_platform.hpp"
#include "kern_xelp_os.hpp"
#include "kern_rpls_memory.hpp"
static bool rplsMemoryAdmitted,rplsMemoryRequested;
#include <cassert>
#include <cstdio>
#include <cstring>
#include <set>
#include <string>
const char *version="Darwin Kernel Version 20.6.0: Thu Jul  6 22:12:47 PDT 2023; root:xnu-7195.141.49.702.12~1/RELEASE_X86_64";
bool noaccel=false;std::set<std::string> extra;
bool checkKernelArgument(const char *s){return (noaccel && !strcmp(s,"-wex-noaccel")) || extra.count(s);}
int kextIntelTGL,kextIntelTGLFb;
bool adlnNativeRCSProfileRequested=false,display13TraceEnabled=false,display13Offline=false;
struct XE {
 XELP::Profile xeProfile;
 bool display12SmallGTDetected=false,adlsDisplaySelected=false;
 bool adlnRequested=false,adlnDetected=false,adlnKernelReady=false,adlnNativeRequested=false;
 bool adlpDisplaySelected=false,adlpRenderRequested=false,display13FramebufferRequested=false;
 bool tglRequested=false,tglAcceleratorRequested=false,tglInactivePorts=false,tglPG1Poll=false;
 bool tglClockOrderRequested=false,tglTrainingLeaseRequested=false,tglProgramEnabled=false;
 int *currentFramebuffer=nullptr,*currentGraphics=nullptr;
 struct {bool available=false;}modDVMTCalcFix;
 void selectProfile(const XELP::Profile &);
};
FUNCTION
int main(){
 const uint32_t mobile[]={0x46a3,0x46a6,0x46a8,0x46aa,0x46b3,0x46c3,0xa7a0,0xa7a1,0xa7a8,0xa7a9,0xa7aa,0xa7ab,0xa7ac,0xa7ad};
 unsigned cases=0;
 for(unsigned which=0;which<30;++which)for(unsigned rev=0;rev<256;++rev)for(unsigned off=0;off<2;++off) {
  noaccel=off;XE x;const bool isMobile=which<28,isN=which==28;
  const auto pci=(isMobile?mobile[which/2]:isN?0x46d1:0x9a49)<<16|0x8086;
  const auto effective=isMobile && (which&1)?0x9a498086:pci;
  const auto p=XELP::identify(pci,rev,effective);x.selectProfile(p);
  assert(XELP::same(x.xeProfile,p) && p.admitted());
  assert(x.currentFramebuffer==&kextIntelTGLFb && x.currentGraphics==&kextIntelTGL);
  assert(x.display13FramebufferRequested==(isMobile || isN));
  assert(x.adlpDisplaySelected==isMobile);
  assert(x.adlpRenderRequested==(isMobile&&!off));
  assert(x.adlnDetected==(isN || (isMobile&&!off)));
  assert(x.tglAcceleratorRequested==!off);
  assert(adlnNativeRCSProfileRequested==(isN || (isMobile&&!off)));++cases;
 }
 noaccel=false;XE unknown;unknown.selectProfile(XELP::identify(0x4c8a8086,12));
 assert(!unknown.adlpRenderRequested && !unknown.adlnDetected && !unknown.tglAcceleratorRequested);

 unsigned rplCases=0;
 for(const char *os:{"Darwin Kernel Version 24.6.0: test/RELEASE_X86_64","Darwin Kernel Version 25.6.0: test/RELEASE_X86_64","Darwin Kernel Version 26.0.0: test/RELEASE_X86_64"})
 for(unsigned rev=0;rev<256;++rev)for(unsigned mode=0;mode<4;++mode){
  version=os;extra.clear();noaccel=mode==2;if(mode==1)extra.insert("-wex-rpls-ggtt-compat-off");if(mode==3)extra.insert("-wex-tgl-off");
  XE target;target.selectProfile(XELP::identify(0xA7808086,rev));const bool yes=rev==4 && XELP::kernelOS(version)==XELP::OS::Tahoe;
  assert(rplsMemoryAdmitted==yes && rplsMemoryRequested==(yes&&mode==0));++rplCases;
 }
 version="Darwin Kernel Version 25.6.0: test/RELEASE_X86_64";extra.clear();noaccel=false;
 for(auto id:{0x46808086U,0xA7888086U,0x9A498086U}){XE target;target.selectProfile(XELP::identify(id,4));assert(!rplsMemoryAdmitted&&!rplsMemoryRequested);}
 {XE target;target.selectProfile(XELP::identify(0xA7808086,4,0x9A498086));assert(!rplsMemoryAdmitted&&!rplsMemoryRequested);}
 assert(rplCases==3072);puts("PASS3072production RPL-S memory-profile cases: every revision, OS, default/off/noaccel/tgl-off, plus wrong hardware/override");
 assert(cases==15360);puts("PASS 15360 production profile selections: all mobile Display13 IDs/revisions, physical and legacy donor selectors, noaccel, ADL-N and TGL");
}
'''.replace('FUNCTION',f)
with tempfile.TemporaryDirectory(prefix='wex-adlp-render-') as d:
 p=Path(d);(p/'test.cpp').write_text(code)
 subprocess.run(['clang++','-std=c++17','-O1','-fsanitize=address,undefined','-I'+str(r/'WhateverXe'),str(p/'test.cpp'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
