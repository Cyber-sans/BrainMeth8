package dev.cybersans.brainmeth;

import net.minecraft.ChatFormatting;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.util.Unit;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.alchemy.PotionContents;
import net.minecraft.world.item.alchemy.Potions;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.item.component.ItemLore;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.common.brewing.IBrewingRecipe;
import net.neoforged.neoforge.event.brewing.RegisterBrewingRecipesEvent;

import java.util.List;
import java.util.Map;
import java.util.Optional;

/** Brewable size potions made from Ant Mandible / Giraffe Neck Hair materials.
 * Ingredients are renamed vanilla brewing ingredients (glowstone, redstone) so
 * clients without this mod still accept them in the brewing stand. Brewed potions
 * use a Thick base, which has no vanilla mixes, so only these recipes apply.
 */
@EventBusSubscriber(modid = BrainmethCore.MOD_ID)
public final class BrainmethBrewing {
    private static final String MARKER = "brainmeth_reward";

    public record Brew(double scale, long seconds, String name, int color, ChatFormatting style) {}

    public static final Map<String, Brew> BREWS = Map.of(
        "brew_shrink",        new Brew(0.5D, 3 * 60, "Potion of Minor Shrinking", 0xB46BFF, ChatFormatting.LIGHT_PURPLE),
        "brew_shrink_long",   new Brew(0.5D, 8 * 60, "Potion of Minor Shrinking", 0xB46BFF, ChatFormatting.LIGHT_PURPLE),
        "brew_shrink_strong", new Brew(0.2D, 90,     "Potion of Strong Shrinking", 0x7A2BD6, ChatFormatting.DARK_PURPLE),
        "brew_grow",          new Brew(1.5D, 3 * 60, "Potion of Minor Growing", 0x6BD66B, ChatFormatting.GREEN),
        "brew_grow_long",     new Brew(1.5D, 8 * 60, "Potion of Minor Growing", 0x6BD66B, ChatFormatting.GREEN),
        "brew_grow_strong",   new Brew(2.0D, 90,     "Potion of Strong Growing", 0x2E9E2E, ChatFormatting.DARK_GREEN)
    );

    private BrainmethBrewing() {}

    private static String kind(ItemStack stack) {
        CustomData data = stack.get(DataComponents.CUSTOM_DATA);
        return data == null ? "" : data.copyTag().getString(MARKER);
    }

    private static boolean isPlain(ItemStack stack, Item item) {
        return stack.is(item) && stack.get(DataComponents.CUSTOM_DATA) == null;
    }

    private static boolean isMarked(ItemStack stack, Item item, String marker) {
        return stack.is(item) && marker.equals(kind(stack));
    }

    private static boolean isAwkward(ItemStack stack) {
        PotionContents contents = stack.get(DataComponents.POTION_CONTENTS);
        return stack.is(Items.POTION) && stack.get(DataComponents.CUSTOM_DATA) == null &&
               contents != null && contents.is(Potions.AWKWARD);
    }

    private static boolean isBrew(ItemStack stack) {
        return stack.is(Items.POTION) && BREWS.containsKey(kind(stack));
    }

    /** Next potion kind for an input and ingredient, or null when nothing brews. */
    static String result(ItemStack input, ItemStack ingredient) {
        if (isAwkward(input)) {
            if (isMarked(ingredient, Items.GLOWSTONE_DUST, "shrink_dust")) return "brew_shrink";
            if (isMarked(ingredient, Items.REDSTONE, "growth_powder")) return "brew_grow";
            return null;
        }
        if (!isBrew(input)) return null;
        String kind = kind(input);
        if (isPlain(ingredient, Items.FERMENTED_SPIDER_EYE)) {
            return kind.contains("shrink") ? kind.replace("shrink", "grow") : kind.replace("grow", "shrink");
        }
        boolean minor = kind.equals("brew_shrink") || kind.equals("brew_grow");
        if (minor && isPlain(ingredient, Items.REDSTONE)) return kind + "_long";
        if (minor && isPlain(ingredient, Items.GLOWSTONE_DUST)) return kind + "_strong";
        return null;
    }

    public static ItemStack potion(String kind) {
        Brew brew = BREWS.get(kind);
        ItemStack potion = new ItemStack(Items.POTION);
        potion.set(DataComponents.POTION_CONTENTS,
            new PotionContents(Optional.of(Potions.THICK), Optional.of(brew.color()), List.of()));
        potion.set(DataComponents.ITEM_NAME, Component.literal(brew.name()).withStyle(brew.style()));
        potion.set(DataComponents.LORE, new ItemLore(List.of(
            Component.literal(sizeText(brew.scale()) + " size for " + durationText(brew.seconds()))
                .withStyle(ChatFormatting.GRAY),
            Component.literal("Time continues while offline.").withStyle(ChatFormatting.DARK_GRAY)
        )));
        potion.set(DataComponents.HIDE_ADDITIONAL_TOOLTIP, Unit.INSTANCE);
        potion.set(DataComponents.ENCHANTMENT_GLINT_OVERRIDE, true);
        CompoundTag data = new CompoundTag();
        data.putString(MARKER, kind);
        potion.set(DataComponents.CUSTOM_DATA, CustomData.of(data));
        return potion;
    }

    static String sizeText(double scale) {
        if (scale == 0.2D) return "One-fifth";
        if (scale == 0.5D) return "Half";
        if (scale == 1.5D) return "One and a half times";
        if (scale == 2.0D) return "Double";
        return scale + "x";
    }

    static String durationText(long seconds) {
        if (seconds % 60 != 0) return seconds + " seconds";
        long minutes = seconds / 60;
        return minutes + (minutes == 1 ? " minute" : " minutes");
    }

    @SubscribeEvent
    public static void onRegisterBrewing(RegisterBrewingRecipesEvent event) {
        event.getBuilder().addRecipe(new IBrewingRecipe() {
            @Override
            public boolean isInput(ItemStack input) {
                return isAwkward(input) || isBrew(input);
            }

            @Override
            public boolean isIngredient(ItemStack ingredient) {
                return isMarked(ingredient, Items.GLOWSTONE_DUST, "shrink_dust") ||
                       isMarked(ingredient, Items.REDSTONE, "growth_powder") ||
                       isPlain(ingredient, Items.REDSTONE) ||
                       isPlain(ingredient, Items.GLOWSTONE_DUST) ||
                       isPlain(ingredient, Items.FERMENTED_SPIDER_EYE);
            }

            @Override
            public ItemStack getOutput(ItemStack input, ItemStack ingredient) {
                String next = result(input, ingredient);
                return next == null ? ItemStack.EMPTY : potion(next);
            }
        });
    }
}
