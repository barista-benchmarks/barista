package org.acme.tika;

import java.io.InputStream;

import jakarta.inject.Inject;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;

import io.quarkus.tika.TikaParser;

@Path("/parse")
public class TikaParserResource {

    @Inject
    TikaParser parser;

    @POST
    @Path("/text")
    @Consumes({ "application/pdf", "application/vnd.oasis.opendocument.text" })
    @Produces(MediaType.TEXT_PLAIN)
    public String extractText(InputStream stream) {
        return parser.getText(stream);
    }

    // We need this empty endpoint because non-wrk measurements (e.g., time to first response) aren't configured to POST a data payload.
    @GET
    @Path("/")
    @Produces(MediaType.TEXT_PLAIN)
    public String hello() {
        return "test";
    }
}
