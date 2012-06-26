package newseman.lucene.whisperer;

import java.util.HashMap;

public class Test {
	public Test(String[] args) {
		System.out.println("ok");
	}
	public HashMap<String, HashMap<String, String>> getPossibleLabels(String query) {
		HashMap<String, HashMap<String, String>> out = new HashMap<String, HashMap<String, String>>();
		
		HashMap<String, String> n = new HashMap<String, String>();
		n.put("#", "01");
		out.put("wave", n);
		
		return out;
	}
	
	public HashMap<String, HashMap<String, String>> 
		getSemesForLabels(HashMap<String, HashMap<String, String>> labels) {
	/* For each entry in the labels finds the corresponding
	 * semes (there may be multiple definitions for the label)
	 * @param labels array of labels
	 * @return array of arrays with the found seme definitions
	 */
	
	labels.get("wave").put(new Double(Math.random()).toString(), "xxx");
	
	return labels;
}
}
