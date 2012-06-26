package newseman.lucene.whisperer;

import org.apache.lucene.index.CorruptIndexException;
import org.apache.lucene.index.IndexWriter;
import org.apache.lucene.index.IndexReader;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.LockObtainFailedException;
import org.apache.lucene.store.SimpleFSDirectory;
import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.analysis.WhitespaceAnalyzer; 
import org.apache.lucene.analysis.KeywordAnalyzer; //spell check works very well, but no searching works then
import org.apache.lucene.document.Document;
import org.apache.lucene.document.Field;

import org.apache.lucene.search.spell.LuceneDictionary;
import org.apache.lucene.search.spell.SpellChecker;

import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.FileReader;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;


/**
 * This code was originally written for
 * Erik's Lucene intro java.net article
 */
public class IndexDictionary {
	/**
	 * Builds a spellchecking/did-you-mean dictionary.
	 * The dictionary is special in that it will allow searching
	 * for similar variants of the search term - most useful
	 * queries will be focused on the key, or key in combination with
	 * the mode. Usually the value contains semes and there we are
	 * not interested in matching similar entries (but boolean is OK).
	 *
	 * Available fields (for returned values) are:
	 *  key
	 *  key-raw
	 *  mode
	 *  value
	 * @param args
	 * @throws Exception
	 */

	/**
	 * @param args
	 * @throws Exception
	 */
	public static void main(String[] args) throws Exception {
		if (args.length != 2) {
			throw new Exception("Usage: java "
					+ IndexDictionary.class.getName()
					+ " <index dir> <input file>");
		}
		long start = new Date().getTime();
		ArrayList<String> files = new ArrayList<String>();
		for (int i=1; i<args.length; i++) {
			files.add((String)args[i]);
		}
		//System.out.println("ok");
		System.out.println("Indexing " + files.toString());

		// int numIndexed = reindexDirectory(indexDir, dataDir);
		int numIndexed = reindexFiles(files, args[0]);

		long end = new Date().getTime();

		System.out.println("Indexing " + numIndexed + " entries took "
				+ (end - start) + " milliseconds");
	}

	public static int reindexFiles(String[] sourceFiles, String indexDir)
			throws CorruptIndexException, LockObtainFailedException,
			IOException {
		ArrayList<String> files = new ArrayList<String>();
		for (int i = 0; i < sourceFiles.length; i++) {
			files.add(sourceFiles[i]);
		}
		return reindexFiles(files, indexDir);

	}

	public static int reindexFiles(ArrayList<String> sourceFiles, String indexDir)
			throws CorruptIndexException, LockObtainFailedException,
			IOException {
		/**
		 * Builds spellchecking dictionary from the supplied files
		 *
		 * @var sourceFiles - String[] with file names
		 * @var indexDir - String, where to build the index
		 *
		 */
		File dir = new File(indexDir);
		IndexWriter writer = getWriter(dir);

		for (String file : sourceFiles) {
			File srcFile = new File(file);
			indexFile(writer, srcFile);
		}
		int numIndexed = writer.numDocs();
		writer.close();

		buildSpellChecker(dir, "key-raw");
        
        writer = getWriter(dir);
        writer.optimize();
		return numIndexed;
	}

	public static int reindexDirectory(File indexDir, File dataDir)
			throws IOException {
		/**
		 * Builds a spellchecking/did-you-mean dictioanary from all the files
		 * inside the directory (and all levels deep) if they end up with
		 * suffix .seman
		 *
		 * @var indexDir - where to build the index
		 * @var dataDir - where to look for files (all files there are
		 *      processed)
		 */

		if (!dataDir.exists() || !dataDir.isDirectory()) {
			throw new IOException(dataDir
					+ " does not exist or is not a directory");
		}

		IndexWriter writer = getWriter(indexDir);

		writer.setMaxFieldLength(100);
		writer.setUseCompoundFile(true);

		indexDirectory(writer, dataDir);

		int numIndexed = writer.numDocs();
		writer.close();

		buildSpellChecker(indexDir, "key-raw");
        
        writer = getWriter(indexDir);
        writer.optimize();
        
		return numIndexed;
	}

	private static IndexWriter getWriter(File indexDir)
			throws CorruptIndexException, LockObtainFailedException,
			IOException {
		Analyzer analyzer = new KeywordAnalyzer(); //WhitespaceAnalyzer();
		Directory dir = new SimpleFSDirectory(indexDir);
		IndexWriter writer = new IndexWriter(dir, analyzer,
				true, IndexWriter.MaxFieldLength.LIMITED);
		return writer;
	}

	private static void buildSpellChecker(File indexDir, String field)
			throws IOException {

		if (!indexDir.exists() || !indexDir.isDirectory()) {
			throw new IOException(indexDir
					+ " does not exist or is not a directory");
		}

		Directory dir = new SimpleFSDirectory(indexDir);

		// build the spell-checking index
		SpellChecker spell = new SpellChecker(dir);
		IndexReader my_indexreader = IndexReader.open(dir, true); // readOnly =
																	// true
		spell.indexDictionary(new LuceneDictionary(my_indexreader, field));
		my_indexreader.close();
	}

	private static void indexDirectory(IndexWriter writer, File dir)
			throws IOException {

		File[] files = dir.listFiles();

		for (int i = 0; i < files.length; i++) {
			File f = files[i];
			if (f.isDirectory()) {
				indexDirectory(writer, f); // recurse
			} else if (f.getName().endsWith(".seman")) {
				indexFile(writer, f);
			}
		}
	}

	private static void indexFile(IndexWriter writer, File f)
			throws IOException {

		if (f.isHidden() || !f.exists() || !f.canRead()) {
			return;
		}

		FileReader fr = new FileReader(f);
		BufferedReader br = new BufferedReader(fr);

		String delimiter = new String("=");
		String s;
		while ((s = br.readLine()) != null) {
			s = s.trim();
			if (s.length() > 0) {
				String[] temp = s.split(delimiter);
				if (temp.length == 2 && temp[0].trim().length() > 0) {
					int space = temp[0].indexOf(" ");
					if (space <= 4) {
						Document doc = new Document();
						doc.add(new Field("mode", temp[0].substring(0, space)
								.trim(), Field.Store.YES,
								Field.Index.NOT_ANALYZED_NO_NORMS));
						doc
								.add(new Field("key", temp[0].substring(
										space + 1).trim(), Field.Store.YES,
										Field.Index.ANALYZED));
						doc.add(new Field("key-raw", temp[0].substring(
								space + 1).trim(), Field.Store.YES,
								Field.Index.NOT_ANALYZED));
						doc.add(new Field("value", temp[1].trim(),
								Field.Store.YES, Field.Index.ANALYZED));
						writer.addDocument(doc);
					} else {
						System.out.println("Error processing entry: " + s);
					}
				}
				else {
					System.out.println("Error processing entry: " + s);
				}
			}
		}
		fr.close();

	}
}