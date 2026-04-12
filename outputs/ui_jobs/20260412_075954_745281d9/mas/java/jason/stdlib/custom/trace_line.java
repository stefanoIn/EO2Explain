package jason.stdlib.custom;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;

import jason.asSemantics.DefaultInternalAction;
import jason.asSemantics.TransitionSystem;
import jason.asSemantics.Unifier;
import jason.asSyntax.StringTerm;
import jason.asSyntax.Term;

// Appends a simple agent conversation line to a plain text log file so the UI
// can show a readable MAS dialogue trace even when Gradle swallows stdout.
public class trace_line extends DefaultInternalAction {
    private static final long serialVersionUID = 1L;

    @Override
    public int getMinArgs() {
        return 2;
    }

    @Override
    public int getMaxArgs() {
        return 2;
    }

    @Override
    public Object execute(TransitionSystem ts, Unifier un, Term[] args) throws Exception {
        String agent = toString(args[0].capply(un));
        String message = toString(args[1].capply(un));

        Path outputFile = Paths.get("..", "logs", "agent_trace.log");
        Files.createDirectories(outputFile.getParent());

        String line = "[" + agent + "] --> " + message + System.lineSeparator();
        Files.writeString(
            outputFile,
            line,
            StandardCharsets.UTF_8,
            StandardOpenOption.CREATE,
            StandardOpenOption.APPEND,
            StandardOpenOption.WRITE
        );
        return true;
    }

    private String toString(Term term) {
        if (term instanceof StringTerm stringTerm) {
            return stringTerm.getString();
        }
        String raw = term.toString();
        if (raw.startsWith("\"") && raw.endsWith("\"") && raw.length() >= 2) {
            return raw.substring(1, raw.length() - 1);
        }
        return raw;
    }
}
