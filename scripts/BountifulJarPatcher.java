import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Enumeration;
import java.util.jar.JarEntry;
import java.util.jar.JarFile;
import java.util.jar.JarOutputStream;
import jdk.internal.org.objectweb.asm.*;

/** Minimal binary patch against the SHA-512-pinned upstream NeoForge beta.2 JAR. */
public final class BountifulJarPatcher {
    private static final String CLASS = "io/ejekta/bountiful/content/BountyCreator.class";
    private static int patched = 0;

    private static byte[] change(byte[] src) {
        ClassReader reader = new ClassReader(src);
        ClassWriter writer = new ClassWriter(reader, ClassWriter.COMPUTE_MAXS);
        reader.accept(new ClassVisitor(Opcodes.ASM9, writer) {
            @Override public MethodVisitor visitMethod(int access, String name, String desc,
                                                       String sig, String[] exceptions) {
                MethodVisitor next = super.visitMethod(access, name, desc, sig, exceptions);
                if (!name.equals("pickFiller") || !desc.startsWith("(Ljava/util/List;DZ)")) return next;
                patched++;
                return new MethodVisitor(Opcodes.ASM9, next) {
                    @Override public void visitCode() {
                        super.visitCode();
                        // minByOrNull selects the FIRST minimum-distance entry. Randomizing
                        // the candidate order makes tied equal-weight entries equiprobable.
                        // Non-ties remain ordered by exactly the same worth-distance rule.
                        // Make a copy: callers may supply an immutable Kotlin List.
                        visitTypeInsn(Opcodes.NEW, "java/util/ArrayList");
                        visitInsn(Opcodes.DUP);
                        visitVarInsn(Opcodes.ALOAD, 1);
                        visitMethodInsn(Opcodes.INVOKESPECIAL, "java/util/ArrayList", "<init>",
                                "(Ljava/util/Collection;)V", false);
                        visitVarInsn(Opcodes.ASTORE, 1);
                        visitVarInsn(Opcodes.ALOAD, 1);
                        visitMethodInsn(Opcodes.INVOKESTATIC, "java/util/Collections", "shuffle",
                                "(Ljava/util/List;)V", false);
                    }
                };
            }
        }, 0);
        return writer.toByteArray();
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 2) throw new IllegalArgumentException("Usage: original.jar patched.jar");
        Path source = Path.of(args[0]), target = Path.of(args[1]);
        if (source.toAbsolutePath().equals(target.toAbsolutePath()))
            throw new IllegalArgumentException("Input and output paths must differ");
        int classes = 0;
        try (JarFile input = new JarFile(source.toFile());
             JarOutputStream output = new JarOutputStream(Files.newOutputStream(target))) {
            Enumeration<JarEntry> entries = input.entries();
            while (entries.hasMoreElements()) {
                JarEntry entry = entries.nextElement();
                String name = entry.getName();
                if (name.matches("META-INF/[^/]+\\.(SF|RSA|DSA|EC)"))
                    throw new IllegalStateException("Refusing to modify a signed JAR");
                byte[] data;
                try (InputStream in = input.getInputStream(entry)) { data = in.readAllBytes(); }
                if (name.equals(CLASS)) { classes++; data = change(data); }
                JarEntry out = new JarEntry(name);
                out.setTime(entry.getTime());
                output.putNextEntry(out);
                if (!entry.isDirectory()) output.write(data);
                output.closeEntry();
            }
        }
        if (classes != 1 || patched != 1) {
            Files.deleteIfExists(target);
            throw new IllegalStateException("Upstream layout changed: classes=" + classes + " methods=" + patched);
        }
        System.out.println("Patched Bountiful 8.0.0-beta.2: shuffled filler candidate list");
    }
}
