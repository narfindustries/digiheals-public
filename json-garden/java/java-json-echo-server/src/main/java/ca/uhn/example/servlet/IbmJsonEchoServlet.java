import jakarta.json.Json;
import jakarta.json.JsonStructure;
import jakarta.json.JsonReader;
import jakarta.json.JsonReaderFactory;
import java.io.IOException;
import org.apache.commons.io.IOUtils;
import com.google.common.base.Charsets;
import org.eclipse.parsson.api.JsonConfig;
import java.util.Collections;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.*;
import jakarta.servlet.*;
import ca.uhn.fhir.rest.server.RestfulServer;
import java.nio.charset.StandardCharsets;
import java.io.StringWriter;
import jakarta.json.JsonWriter;

@WebServlet("/ibmecho")
public class IbmJsonEchoServlet extends RestfulServer {
    private static final long serialVersionUID = 1L;
    private static final JsonReaderFactory JSON_READER_FACTORY = Json.createReaderFactory(Collections.singletonMap(JsonConfig.REJECT_DUPLICATE_KEYS, true));
    protected void doPost(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
	// String body = IOUtils.toString(request.getInputStream(), Charsets.UTF_8);
	JsonReader jsonReader = JSON_READER_FACTORY.createReader(request.getInputStream(), StandardCharsets.UTF_8);
	JsonStructure jsonStructure = jsonReader.read();
	StringWriter stWriter = new StringWriter();
	JsonWriter jsonWriter = Json.createWriter(stWriter);
	jsonWriter.write(jsonStructure);
	jsonWriter.close();
	response.setContentType("text/plain; charset=UTF-8");
	response.getWriter().write(stWriter.toString());
	response.getWriter().close();

    }

}
