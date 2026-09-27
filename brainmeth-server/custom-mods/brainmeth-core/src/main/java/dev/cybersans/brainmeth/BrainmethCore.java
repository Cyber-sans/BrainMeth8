package dev.cybersans.brainmeth;

import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.ModContainer;
import net.neoforged.fml.common.Mod;
import org.slf4j.Logger;
import com.mojang.logging.LogUtils;

@Mod(BrainmethCore.MOD_ID)
public final class BrainmethCore {
    public static final String MOD_ID = "brainmeth_core";
    public static final Logger LOGGER = LogUtils.getLogger();

    public BrainmethCore(IEventBus modBus, ModContainer modContainer) {
        LOGGER.info("Brainmeth Core loaded");
    }
}
