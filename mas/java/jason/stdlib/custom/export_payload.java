package jason.stdlib.custom;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;

import jason.asSemantics.DefaultInternalAction;
import jason.asSemantics.TransitionSystem;
import jason.asSemantics.Unifier;
import jason.asSyntax.ASSyntax;
import jason.asSyntax.Term;

// Writes a ground Jason term as JSON so it can be consumed later by the
// external Python/OWL layer. The term already implements Jason's ToJson API.
public class export_payload extends DefaultInternalAction {
    private static final long serialVersionUID = 1L;

    @Override
    public int getMinArgs() {
        return 2;
    }

    @Override
    public int getMaxArgs() {
        return 3;
    }

    @Override
    protected void checkArguments(Term[] args) {
        // No extra checks beyond arity; the payload is expected to be ground.
    }

    @Override
    public Object execute(TransitionSystem ts, Unifier un, Term[] args) throws Exception {
        Term eventTerm = args[0].capply(un);
        Term payloadTerm = args[1].capply(un);

        String eventId = sanitizeFileStem(eventTerm.toString());
        Path outputDir = Paths.get("..", "outputs", "semantic_explanations");
        Files.createDirectories(outputDir);

        Path outputFile = outputDir.resolve(eventId + ".json");
        String json = payloadTerm.getAsJsonStr();

        Files.writeString(
            outputFile,
            json + System.lineSeparator(),
            StandardCharsets.UTF_8,
            StandardOpenOption.CREATE,
            StandardOpenOption.TRUNCATE_EXISTING,
            StandardOpenOption.WRITE
        );

        if (args.length == 3) {
            return un.unifies(args[2], ASSyntax.createString(outputFile.toString()));
        }
        return true;
    }

    private String sanitizeFileStem(String raw) {
        String normalized = raw;
        if (normalized.startsWith("\"") && normalized.endsWith("\"") && normalized.length() >= 2) {
            normalized = normalized.substring(1, normalized.length() - 1);
        }
        return normalized.replaceAll("[^A-Za-z0-9._-]", "_");
    }
}
