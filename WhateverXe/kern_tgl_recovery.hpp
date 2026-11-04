// Exact TGL donor layout, with the native ICL single-pass recovery contract.
// The caller must qualify the binary and select host scheduler 5 first.
#ifndef kern_tgl_recovery_hpp
#define kern_tgl_recovery_hpp
#include <stdint.h>

namespace TGLRecovery {
template<typename T> inline T &field(void *p, unsigned offset) {
	return *reinterpret_cast<T *>(static_cast<uint8_t *>(p)+offset);
}

struct Result {
	uintptr_t ring, context, affected;
	uint32_t index, failuresBefore, failuresAfter;
	bool resetOK;
	uint32_t attempts;
	uintptr_t activeBefore, activeAfter;
};

// ICL resetHardwareAndReplay: reset once, account a native
// failure, resume scheduling, return to IOAccel's error/event processing.
// TGL's lower reset still owns hardware reset, context replay and CSB handling.
// Do not append a new stamp or wait inside this recovery work-loop callback.
inline Result resetAndResume(void *channel) {
	void *ring=field<void *>(channel,0x130);
	void *context=field<void *>(ring,0x20);
	void *affected=field<void *>(context,0xB8); // ICL uses B0, NOT compatible.
	Result result {reinterpret_cast<uintptr_t>(ring),reinterpret_cast<uintptr_t>(context),
		reinterpret_cast<uintptr_t>(affected),field<uint32_t>(affected,0x20),
		field<uint32_t>(affected,0x17C),0,false,0,0,0};
	using Reset=bool (*)(void *,void *);
	// TGL resetGraphicsEngine (43576) first tries the engine's pending soft
	// steps (engine+0xA4 bits 3/2). When the engine does not acknowledge one
	// it clears that bit and returns success WITHOUT resetting, so the hung
	// batch is never dropped and IOAccel restarts the channel forever. Native
	// callers loop until a stamp lands; repeat only while a soft step was
	// pending, so the full GDRST path and processGPUReset (resetRing plus the
	// completing stamp) run in this pass.
	auto engineFlags=[&]() -> uint32_t {
		void *engine=field<void *>(ring,0x8B8+8*field<uint8_t>(ring,0x40));
		return engine ? field<uint32_t>(engine,0xA4)&0xC : 0;
	};
	// IGHardwareCommandStreamer5::processGPUReset only drops the hung batch
	// (resetRing + resubmitStampToRing) through the active port element.
	// IGScheduler5::processGPUReset(type) -> scheduler+0xCA0[type].
	auto active=[&]() -> uintptr_t {
		void *accelerator=field<void *>(ring,0x10);
		void *scheduler=accelerator ? field<void *>(accelerator,0x1250) : nullptr;
		void *streamer=scheduler ? field<void *>(scheduler,0xCA0+8*field<uint8_t>(ring,0x40)) : nullptr;
		if (!streamer) return 1;
		const uint32_t port=field<uint32_t>(streamer,0x50);
		return (field<uintptr_t>(streamer,0x30+16*(port&1))&~uintptr_t(0xF)) |
			(field<uintptr_t>(streamer,0x30+16*(1-(port&1))) ? 4 : 0) | (port&3);
	};
	result.activeBefore=active();
	for (unsigned attempt=0;attempt<3;++attempt) {
		const bool soft=engineFlags()!=0;
		result.resetOK=field<Reset>(field<void *>(ring,0),0x168)(ring,context);
		result.attempts=attempt+1;
		if (!soft || !result.resetOK) break;
	}
	result.activeAfter=active();
	if (!result.resetOK) ++field<uint32_t>(affected,0x17C);
	result.failuresAfter=field<uint32_t>(affected,0x17C);
	// Reload after reset, as the native ICL caller does.
	void *owner=field<void *>(channel,0x18);
	void *scheduler=field<void *>(owner,0x1250); // ICL uses1280.
	using Resume=void (*)(void *);
	field<Resume>(field<void *>(scheduler,0),0x180)(scheduler);
	return result;
}
}
#endif
