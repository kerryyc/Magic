package magic;

import okhttp3.Request;
import okhttp3.Response;
import okhttp3.OkHttpClient;
import java.io.IOException;

public class Magic {
	private final OkHttpClient httpClient = new OkHttpClient();
	
	public static void main(String args[]) throws Exception {
		System.out.println("Hello World");
		
		Magic obj = new Magic();

        System.out.println("Testing 1 - Send Http GET request");
        obj.sendGet("https://api.scryfall.com/cards/search?q=c%3Awhite+cmc%3D1");
	}
	
	private void sendGet(String url) throws Exception {

        Request request = new Request.Builder()
                .url(url)
                .build();
        try (Response response = httpClient.newCall(request).execute()) {
            // Get response body
            System.out.println(response.body().string());
        }
	}
}
