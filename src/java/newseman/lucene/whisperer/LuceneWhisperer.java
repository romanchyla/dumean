package newseman.lucene.whisperer;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.Map.Entry;

import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.document.Document;
import org.apache.lucene.index.IndexReader;
import org.apache.lucene.index.Term;
import org.apache.lucene.queryParser.ParseException;
import org.apache.lucene.queryParser.QueryParser;
import org.apache.lucene.search.BooleanClause;
import org.apache.lucene.search.BooleanQuery;
import org.apache.lucene.search.IndexSearcher;
import org.apache.lucene.search.PhraseQuery;
import org.apache.lucene.search.Query;
import org.apache.lucene.search.ScoreDoc;
import org.apache.lucene.search.Searcher;
import org.apache.lucene.search.TermQuery;
import org.apache.lucene.search.TopScoreDocCollector;
import org.apache.lucene.search.spell.SpellChecker;
import org.apache.lucene.store.FSDirectory;
import org.apache.lucene.util.Version;

/**
 * @author rca
 *
 */
public class LuceneWhisperer {

	private String defaultField = "key";
	private String indexDir;
	private FSDirectory store;
	private Searcher searcher;
	private IndexReader reader;
	private Analyzer analyzer;
	private QueryParser parser;
	private int maxHits = 100;
	private String delimiter = " ";
	private String[] fields = {"key", "mode", "value"};
	private SpellChecker spelldict = null;

	public LuceneWhisperer(String indexDir, String[] savedFields) throws IOException {
		/*
		 * Initializes the class
		 * @param indexDir - string, folder where the lucene index is/should be
		 * @param savedFields - String[], names of fields to return for each record
		 */
		this.indexDir = indexDir;
		if (savedFields.length > 0) {
	    	this.fields = savedFields;
	    }
		this.connect(this.indexDir);
	}

	public LuceneWhisperer(String indexDir) throws IOException {
		/*
		 * Initializes the class using only the path to the folder
		 * (lucene index)
		 */

		this.indexDir = indexDir;
		this.connect(this.indexDir);
	}

	public void connect(String indexDir) throws IOException {
		/*
		 * Connects to the Lucene index, in the read-only mode
		 * @param indexDir: string, path to the lucene folder
		 *
		 */

		this.store = FSDirectory.open(new File(indexDir));
	    this.reader = IndexReader.open(store, true); // only searching, so read-only=true
	    this.searcher = new IndexSearcher(reader);
	    this.analyzer = new StandardAnalyzer(Version.LUCENE_CURRENT);
	    this.parser = new QueryParser(Version.LUCENE_CURRENT, this.defaultField, this.analyzer);
	    this.spelldict = new SpellChecker(store);
	}

	public void close() throws IOException {
		this.store.close();
		this.reader.close();
		//System.out.println("index closed");
	}


	public HashMap<String, HashMap<String, Object>>
		getSuggestions(String queryString, int maxSuggestions) throws ParseException, IOException {
		/*
		 * Finds the most probable labels for the given input - it does so using
		 * Lucene spellchecker, it is searching inside the keys.
		 * @param query - string, input from the user (for now, no elaborate parsing is done)
		 * @return composite object {label : {
		 * 									'#pos': int, labels can be sorted by it },
		 * 							 label2...
		 * 							}
		 */


		HashMap<String, HashMap<String, Object>> out = new HashMap<String, HashMap<String, Object>>();
		ArrayList<String> suggestions = new ArrayList<String>();

		Query query = this.parseQuery(queryString);

		// first try the whole string, search inside the key field
		String first[];
		try {
			first = this.spelldict.suggestSimilar(query.toString("key"), maxSuggestions);
		} catch (IOException e) {
			e.printStackTrace();
			System.err.println("Reconnecting...");
			this.connect(this.indexDir);
			first = this.spelldict.suggestSimilar(query.toString("key"), maxSuggestions);
		}
		if (first.length > 0) {
			for (int i=0; i < first.length; i++) {
				suggestions.add(first[i]);
			}
		}
		else {
			HashSet<Term> terms = new HashSet <Term>();
			query.extractTerms(terms);
			Iterator<Term> iterator = terms.iterator();

			// TODO - search for combinations, discard the simple cases
			while (iterator.hasNext()) {
				Term term = iterator.next();
				String t[];

				try {
					t = spelldict.suggestSimilar(term.text(), maxSuggestions);
				} catch (IOException e) {
					e.printStackTrace();
					System.err.println("Reconnecting...");
					this.connect(this.indexDir);
					t = spelldict.suggestSimilar(term.text(), maxSuggestions);
				}

				for (int i=0; i < t.length; i++) {
					suggestions.add(t[i]);
				}

			}
		}

		if (suggestions.size() > 0) {
			for (int i=0; i < suggestions.size(); i++) {
				HashMap<String, Object> n = new HashMap<String, Object>();
				n.put("#pos", i);
				out.put(suggestions.get(i), n);
			}
		}
		return out;
	}

	public ArrayList<ArrayList> findSimilarByWord(String word, int max) throws Throwable {
		/*
		 * Finds information about the word and retrieve the similar items that
		 * correspond to the semes of the identified word. This is a shortcut to the
		 * 	1. addInfoToLabels
		 * 	2. getSimilarBySem
		 * @param word: string, this word should exist in the key-raw index (if you are unsure
		 * 		then you should use the getSuggestions() to help you find the right label)
		 * @param max: int, how many semilar items shall we retrieve
		 * @return: list of items, the first contains in
		 */

		ArrayList<ArrayList> results = new ArrayList<ArrayList>();

		HashMap<String, HashMap<String, Object>> out = new HashMap<String, HashMap<String, Object>>();
		HashMap<String, Object> empty = new HashMap<String, Object>();

		ArrayList<String> seen = new ArrayList<String>();

		empty.put("#pos", 0);
		out.put(word, empty);

		this.addInfoToLabels(out);

		ArrayList info = (ArrayList) out.get(word).get("info");

		for (int i=0; i < info.size(); i++) {
			String sem = ((HashMap<String,String>) info.get(i)).get("value");
			if (seen.indexOf(sem) < 0) {
				seen.add(sem);
				ArrayList<HashMap> this_info = new ArrayList<HashMap>();
				this_info.add((HashMap) info.get(i));
				results.add(this_info);
				results.add(this.getSimilarBySem(sem, max));
			}
		}

		return results;
	}

	public void addInfoToLabels(HashMap<String, HashMap<String, Object>> labels) throws IOException {
		/*
		 * For each entry in the labels finds the corresponding
		 * values using the key(word)
		 * (there may be multiple definitions for the label)
		 * @param labels array of labels
		 * @return nothing, it writes directly into the supplied HashMap
		 * It will look like this:
		 *      {label : {
		 * 		    #pos': int, labels can be sorted by it
		 * 			info: [
		 * 					{key=label, mode=hqs, value=abd dde, score=...},
		 * 					{key=label, mode=hqs, value=abd xxx, score=...}
		 * 			}
		 * 	     label2 : {
		 * 			#pos': ...
		 * 		}
		 */

		String searchableField = "key-raw";

		for (String label : labels.keySet()) {

			PhraseQuery query = new PhraseQuery();
			query.add(new Term(searchableField, label));

			HashMap pointer = labels.get(label);
			ArrayList<HashMap> results = new ArrayList<HashMap>();
			try {
				results = this.doQuery(query, this.maxHits);
			} catch (IOException e) {
				e.printStackTrace();
				System.err.println("Trying to reconnect...");
				this.connect(this.indexDir);
				results = this.doQuery(query, this.maxHits);
			}

			if (results.size() > 0) {
				pointer.put("info", results);
			}

		}
	}

	public ArrayList<HashMap> getSimilarBySem(String semes, int max) throws IOException {
		String[] items = semes.split("\\s+");
		return this.getSimilarBySem(items, max);

	}

	public ArrayList<HashMap> getSimilarBySem(String[] semes, int max) throws IOException {
		/*
		 * Finds all items that share at least one semes of the semes
		 * that are supplied.
		 * @return array of records (sorted by relevance - which is computed by
		 * 		lucene). Records are basically a dictionary where key is name
		 * 		of the field
		 */

		String searchableField = "value";

		HashMap<String, ArrayList<String>> out = new HashMap<String, ArrayList<String>>();

		StringBuilder sb = new StringBuilder();

		BooleanQuery query = new BooleanQuery();
		for (String o : semes){
			TermQuery t = new TermQuery(new Term(searchableField, o));
			query.add(t, BooleanClause.Occur.SHOULD);
		}

		//System.out.println(semes);
		//System.out.println(query.toString());

		ArrayList<HashMap> results = new ArrayList<HashMap>();
		try {
			results = this.doQuery(query, max);
		} catch (IOException e) {
			e.printStackTrace();
			System.err.println("Retrying to connect...");
			this.connect(this.indexDir);
			results = this.doQuery(query, max);
		}

		return results;

	}

	private Query parseQuery(String s) throws ParseException {
		/*
		 * Creates a query object out of a string - the string can
		 * follow the lucene conventions.
		 */
		Query q = this.parser.parse(s);
		return q;
	}

	public ArrayList<HashMap> doQuery(String line, int max) throws IOException, ParseException {
		Query query = this.parseQuery(line);
		return this.doQuery(query, max);
	}

	public ArrayList<HashMap> doQuery(Query query, int max) throws IOException {
		/*
		 * Asks Lucene to return results -
		 * @param query: query object
		 * @param max: int, number of hits to return
		 *
		 * if something is found it will be stored in the form:
		 * [ {key=term, score=score, value='abd dde', mode='....},
		 *   {key=term2, score=score, value='abd dde', mode='....},...]
		 * @return	: list of results, sorted by the Lucene score (best at top)
		 */

	    TopScoreDocCollector collector = TopScoreDocCollector.create(max, true);
	    this.searcher.search(query, collector);
	    ScoreDoc[] hits = collector.topDocs().scoreDocs;
	    int numTotalHits = collector.getTotalHits();

	    ArrayList<HashMap> out = new ArrayList<HashMap>(numTotalHits);

	    for (int i=0; i < hits.length; i++) {
		    Document doc = searcher.doc(hits[i].doc);
		    HashMap<String, Object> oneDoc = new HashMap<String, Object>();
		    for (String key : this.fields) {
		    	StringBuffer r = new StringBuffer();
		    	for (String f : doc.getValues(key)) {
		    		r.append(f);
		    		r.append(this.delimiter);
		    	}
		    	oneDoc.put(key, r.toString().trim());
		    }
		    oneDoc.put("doc", hits[i].doc);
		    oneDoc.put("score", hits[i].score);
		    out.add(oneDoc);
	    }
	    return out;
	}

	public int getMaxHits() {
		return this.maxHits;
	}

	public int setMaxHits(int maxHits) {
		this.maxHits = maxHits;
		return this.maxHits;
	}

	public void setAccuracy(float acc) {
		if (this.spelldict != null) {
			this.spelldict.setAccuracy(acc);
		}
	}

	protected void finalize() {
		try {
			this.reader.close();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}
	
	public static void testSearch(LuceneWhisperer worker, String word, int max) throws Throwable {
		HashMap<String, HashMap<String, Object>> simple = worker.getSuggestions(word, max);
		System.out.println("Searchin for: " + word);
		Set<Entry<String, HashMap<String, Object>>> vals = simple.entrySet();
		Iterator<Entry<String, HashMap<String, Object>>> it = vals.iterator();
		while (it.hasNext()) {
			System.out.println(it.next());
		}
		
	}

	public static void main(String[] args) throws Throwable {
		String[] saved = {"key", "mode", "value"};
		try {

			LuceneWhisperer worker = new LuceneWhisperer(args[0], saved);
			testSearch(worker, "particle", 1000);
			testSearch(worker, "partial waves", 1000);
			
			

			//find candidates
			String input = "partticle";
			HashMap<String, HashMap<String, Object>> candidates = worker.getSuggestions(input, 8);

			worker.addInfoToLabels(candidates);

			String[] semes = {"00001", "0003y"};
			ArrayList results = worker.getSimilarBySem(semes, 40);

			System.out.println(candidates);
			System.out.println(results);


		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}
}
