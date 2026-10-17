package dev.cybersans.brainmeth;

import net.minecraft.ChatFormatting;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomData;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;
import java.time.Instant;

@EventBusSubscriber(modid=BrainmethCore.MOD_ID)
public final class BrainmethWisdom {
    private static final String[] QUOTES = {
        "A fresh start will put you on your way.",
        "In order to take, one must first give.",
        "Now is the time to try something new.",
        "Take the high road.",
        "Welcome” is a powerful word.",
        "When your heart is pure, your mind is clear.",
        "Someone you care about seeks reconciliation.",
        "Practice makes perfect.",
        "Don’t just think, act!",
        "An important person will offer you support.",
        "You will be pleasantly surprised tonight.",
        "Your mind is your greatest asset.",
        "It is a good time to amend loose ends.",
        "Better ask twice than lose yourself once.",
        "An old friend will swing by.",
        "Always remember to breathe.",
        "Look at the horizon and steady yourself.",
        "Words can hold more power than a sword.",
        "Stop and smell the flowers.",
        "Look within for the truth you seek.",
        "Secret secrets are no fun. Secret secrets hurt someone.",
        "Don't lose your path before the journey begins.",
        "A broken clock is right twice a day, but it's still broken.",
        "Fortune smiles on those who prepare.",
        "Pass on good vibes. The people around may do the same.",
        "Sometimes it's best to walk away.",
        "A single wave hello can turn the fate of the day.",
        "Nothing is lost just because it's not where it used to be.",
        "It's not easy facing up, when your whole world is black.",
        "Can't hold on or life won't change.",
        "Loose lips sink ships.",
        "All you need is kill.",
        "What's that behind you?",
        "Open your eyes, then open your eyes again.",
        "Those with knowledge don't predict, and those that predict don't have knowledge.",
        "The journey of a thousand miles begins with the first step.",
        "Important decisions should be treated trivially, and trivial decisions treated with great importance.",
        "You're lonely, aren't you?",
        "A watched caldron never boils.",
        "Breathe deeply.",
        "You may catch no fish all day, but then catch many at once.",
        "It is up to you.",
        "Brew some tea and expect company.",
        "Let go.",
        "You have to give to receive.",
        "Home is where the heart is. Are you lost?",
        "They miss you. Do you?",
        "Gold slips easily between fingers.",
        "Something wicked this way comes.",
        "Never trust a bald elf.",
        "Do not eat the cookie.",
        "Disregard last the last fortune.",
        "Speak softly, and carry a big stick.",
        "When you look into your own eyes, what do you see?",
        "A test of faith is on the horizon.",
        "Sticks and stones can break your bones, but so can certain words.",
        "Birds of a feather stick together.",
        "Real eyes realize real lies.",
        "No one leaves this place alive. But not all in this place have lived.",
        "The swallow may fly south with the sun or the house martin or the plover may seek warmer climes in winter.",
        "You don’t vote for a king.",
        "Who do you think you are?",
        "A group achieves success when it becomes greater than the sum of its parts.",
        "The early bird catches the worm.",
        "A fool with a tool is still a fool.",
        "Talk is silver, silence is gold.",
        "You get what you get, and you don't get upset.",
        "There's always a little more innocence left to lose.",
        "Don't be caught beneath a turning wheel.",
        "The seed only grows if it is planted deep enough.",
        "You could count a leopard's spots, but what good would that do?",
        "What's the difference between a big shed and a small cabin?",
        "Something is exactly what it seems.",
        "You will be taking a vacation of vacations.",
        "Be unbound from your inhibitions.",
        "Live this day, as if it were your first.",
        "May the stars shine upon you.",
        "Surrender yourself to a lower power.",
        "A leopard cannot change their shorts.",
        "3 is the lucky number.",
        "Don't eat yellow snow.",
        "A new star is rising.",
        "A chain is only as strong as its weakest link.",
        "If you want something done, give it to someone who is busy.",
        "You may be feeling run down, always in the same old rut.",
        "Sometimes the moon is full, other times it's a crescent, other times it's almost full, but it's always the same moon.",
        "Don't look directly at the sun.",
        "Take some time for yourself every now and again.",
        "What's stopping you?",
        "What's forcing you?",
        "This calls for decisiveness.",
        "Remember, no matter where you go, there you are.",
        "Always salt your pasta while boiling it.",
        "Nothing is exactly as it seems.",
    };
    private BrainmethWisdom() {}
    @SubscribeEvent
    public static void onUse(PlayerInteractEvent.RightClickItem event) {
        if(event.getHand()!=InteractionHand.MAIN_HAND ||
            !(event.getEntity() instanceof ServerPlayer player) ||
            !(event.getLevel() instanceof ServerLevel level)) return;
        ItemStack paper=event.getItemStack();
        CustomData custom=paper.get(DataComponents.CUSTOM_DATA);
        if(!paper.is(Items.PAPER)||custom==null ||
            !"book_of_wisdom".equals(custom.copyTag().getString("brainmeth_reward")))return;
        event.setCanceled(true);
        event.setCancellationResult(InteractionResult.SUCCESS);
        CompoundTag tag=custom.copyTag();
        long now=Instant.now().getEpochSecond();
        long ready=tag.getLong("wisdom_ready");
        if(ready>now) {
            player.displayClientMessage(Component.literal("Book of Wisdom: No uses left."),true);
            return;
        }
        tag.putLong("wisdom_ready",now+3600L);
        paper.set(DataComponents.CUSTOM_DATA,CustomData.of(tag));
        String quote=QUOTES[level.random.nextInt(QUOTES.length)];
        level.getServer().getPlayerList().broadcastSystemMessage(
            Component.literal("<Wanda> "+quote).withStyle(ChatFormatting.LIGHT_PURPLE),false);
    }
}
