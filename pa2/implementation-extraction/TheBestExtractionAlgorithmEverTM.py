from bs4 import BeautifulSoup
from difflib import SequenceMatcher
import numpy as np
from scipy.cluster.hierarchy import linkage, fcluster
import json


# Step 1: Parsing the page
def parse_page(html):
    soup = BeautifulSoup(html, 'html.parser')
    soup_tags = soup.find_all(True)
    layout_blocks = []
    recursive_tags = []
    for tag in soup_tags:
        recursive_tags.append(tag.name)
        text_content = str(tag.decode_contents())
        #print(text_content)
        
        if len(text_content) > 0:
            if text_content[0] in ["<"," ","\n","\xa0","_","."] or tag.name in ["script", "meta", "link"]:
                #recursive_tags.pop()
                pass
            else:
                layout_blocks.append([recursive_tags, tag.get_text()])
                recursive_tags.pop()
                recursive_tags = []
        else: 
            recursive_tags.pop()


    #text = soup.stripped_strings
    #blocks = [str(t) for t in text]
    #print(layout_blocks)
    return str(layout_blocks)

# Step 2: Computing similarity
def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def compute_similarity_matrix(pages):
    n = len(pages)
    sim_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i != j:
                sim_matrix[i, j] = similarity(" ".join(pages[i]), " ".join(pages[j]))
    return sim_matrix


# Step 3: Clustering and generating a layout pattern
def cluster_pages(similarity_matrix, threshold):
    clusters = fcluster(linkage(similarity_matrix, method='single'), threshold, criterion='distance')
    return clusters

# Step 4: Removing banners and navigation links
def compute_diff_scores(layout_blocks):
    n = len(layout_blocks)
    if n <= 1:
        return np.zeros(n)

    diff_scores = np.zeros(n)
    for i in range(n):
        for j in range(n):
            if i != j:
                diff_scores[i] += similarity(layout_blocks[i], layout_blocks[j])
        diff_scores[i] /= (n - 1)
    return diff_scores

def remove_static_blocks(layout_blocks, diff_scores, threshold):
    dynamic_blocks = [block for block, score in zip(layout_blocks, diff_scores) if score > threshold]
    return dynamic_blocks

# Step 5: Discovering the title and main text
def find_title_and_main_text(layout_blocks, diff_scores, title_threshold, main_text_threshold):
    title = None
    main_text = []

    max_score = 0
    max_idx = 0
    for idx, score in enumerate(diff_scores):
        if score > max_score:
            max_score = score
            max_idx = idx

    if max_score > title_threshold:
        title = layout_blocks[max_idx]

    for block, score in zip(layout_blocks, diff_scores):
        if block != title and score > main_text_threshold:
            main_text.append(block)

    return title, main_text

def create_wrapper(results):
    wrapper = []
    for res in results:
        wrapper.append({
            'cluster_id': int(res['cluster_id']),
            'title': res['title'],
            'main_text': res['main_text']
        })
    return json.dumps(wrapper, indent=2)

def webstemmer(html_page1,html_page2, sim_threshold, diff_threshold, title_threshold, main_text_threshold):
    html_pages = [html_page1, html_page2]
    # Step 1: Parsing the page
    parsed_pages = [parse_page(html) for html in html_pages]

    # Step 2: Computing similarity
    sim_matrix = compute_similarity_matrix(parsed_pages)

    # Step 3: Clustering and generating a layout pattern
    clusters = cluster_pages(sim_matrix, sim_threshold)

    results = []
    for cluster_id in set(clusters):
        cluster_indices = [i for i, c in enumerate(clusters) if c == cluster_id]
        cluster_blocks = [parsed_pages[i] for i in cluster_indices]

        diff_scores = compute_diff_scores(cluster_blocks)

        dynamic_blocks = remove_static_blocks(cluster_blocks, diff_scores, diff_threshold)

        title, main_text = find_title_and_main_text(dynamic_blocks, diff_scores, title_threshold, main_text_threshold)

        results.append({
            'cluster_id': cluster_id,
            'title': title,
            'main_text': main_text
        })

        wrappd_results = create_wrapper(results)

        return wrappd_results
