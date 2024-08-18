package com.example.mixin;

import com.example.testThread;
import net.minecraft.registry.RegistryKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.world.World;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import java.util.Map;

@Mixin(MinecraftServer.class)
public class ExampleMixin {
	@Shadow @Final private Map<RegistryKey<World>, ServerWorld> worlds;

	@Inject(at = @At("HEAD"), method = "loadWorld")
	private void init(CallbackInfo info) {

		Thread thread = new testThread(worlds);
		thread.start();
		// This code is injected into the start of MinecraftServer.loadWorld()V
	}
}