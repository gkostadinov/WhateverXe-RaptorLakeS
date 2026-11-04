#include "../WhateverXe/kern_tgl_recovery.hpp"
#include <cassert>
#include <cstdio>
#include <cstring>
#include <initializer_list>

namespace {
alignas(16) uint8_t channel[0x180],affected[0x180],ring[0x900],context[0xD0],engine[0x100];
alignas(16) uint8_t owner[0x1300],scheduler[0x200],otherScheduler[0x200];
alignas(16) uint8_t ringVT[0x200],schedulerVT[0x200];
unsigned resets,resumes,stage;bool nativeOK,replaceScheduler;
bool reset(void *r,void *c) {
	assert(r==ring && c==context && stage==0);++resets;
	// Native side effects must survive. No caller-synthesized completion.
	TGLRecovery::field<uint32_t>(affected,0x178)=0xABCDEF;
	if (replaceScheduler) TGLRecovery::field<void *>(owner,0x1250)=otherScheduler;
	auto &flags=TGLRecovery::field<uint32_t>(engine,0xA4);
	// The donor clears one pending soft step and returns without resetting.
	if (flags&8) {flags&=~8U;return nativeOK;}
	if (flags&4) {flags&=~4U;return nativeOK;}
	stage=1;
	return nativeOK;
}
void resume(void *s) {
	assert(s==(replaceScheduler ? otherScheduler : scheduler));
	assert(stage==1 || !nativeOK);stage=2;++resumes;
}
}
int main() {
	unsigned cases=0;
	for (unsigned soft:{0U,4U,8U,12U}) for (bool ok:{false,true}) for (bool replace:{false,true}) for (unsigned initial:{0U,5U,0xFFFFFFFFU}) {
		memset(channel,0,sizeof(channel));memset(affected,0,sizeof(affected));
		TGLRecovery::field<void *>(channel,0x130)=ring;
		TGLRecovery::field<void *>(channel,0x18)=owner;
		TGLRecovery::field<void *>(ring,0)=ringVT;
		TGLRecovery::field<void *>(ring,0x20)=context;
		TGLRecovery::field<uint8_t>(ring,0x40)=0;
		TGLRecovery::field<void *>(ring,0x8B8)=engine;
		TGLRecovery::field<uint32_t>(engine,0xA4)=soft|0x30; // unrelated bits survive
		TGLRecovery::field<void *>(context,0xB8)=affected;
		TGLRecovery::field<void *>(owner,0x1250)=scheduler;
		TGLRecovery::field<void *>(scheduler,0)=schedulerVT;
		TGLRecovery::field<void *>(otherScheduler,0)=schedulerVT;
		TGLRecovery::field<decltype(&reset)>(ringVT,0x168)=reset;
		TGLRecovery::field<decltype(&resume)>(schedulerVT,0x180)=resume;
		TGLRecovery::field<uint32_t>(affected,0x20)=2;
		TGLRecovery::field<uint32_t>(affected,0x17C)=initial;
		nativeOK=ok;replaceScheduler=replace;resets=resumes=stage=0;
		const auto result=TGLRecovery::resetAndResume(channel);
		const unsigned pending=__builtin_popcount(soft);
		// A failed native reset stops; a pending soft step is retried until
		// the full reset ran (at most three attempts).
		const unsigned expected=ok ? pending+1 : 1;
		assert(resets==expected && result.attempts==expected && resumes==1 && stage==2 && result.resetOK==ok);
		if (ok) assert(TGLRecovery::field<uint32_t>(engine,0xA4)==0x30);
		++cases;
		assert(result.affected==reinterpret_cast<uintptr_t>(affected) && result.index==2);
		assert(result.failuresBefore==initial && result.failuresAfter==initial+unsigned(!ok));
		assert(TGLRecovery::field<uint32_t>(affected,0x178)==0xABCDEF);
		// Affected channel comes from the context; do not update caller blindly.
		assert(TGLRecovery::field<uint32_t>(channel,0x17C)==0);
	}
	printf("%u recovery cases passed: soft-step retry, native result, count, order, affected channel, owner reload\n",cases);
}
