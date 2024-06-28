import jakarta.servlet.annotation.WebServlet;
import com.fasterxml.jackson.databind.ObjectMapper;

@WebServlet("/openmrsecho")
public class OpenMrsJsonEcho extends RawJsonEchoServlet {

    public ObjectMapper getObjectMapper() {
	ObjectMapper o = new ObjectMapper();
	o.getFactory().setCharacterEscapes(new OpenmrsCharacterEscapes());
	return o;
    }

}
