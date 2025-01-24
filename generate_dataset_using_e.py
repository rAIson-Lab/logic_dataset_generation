import io
import subprocess
import pickle
import copy
import gzip
import tqdm

if __name__=="__main__":
    file_path = "f.tptp"
    eprover_path = "/home/anmarch/source/eprover/PROVER/eprover"
    variables = ['a', 'b', 'c']
    number_of_disjunctions_to_add  = 1
    number_of_conjunctions_to_add = 1


    literals = []
    for element in variables:
            literals.append(element)
            literals.append('~'+element)

    disjunctions = copy.deepcopy(literals)

    for _ in range(number_of_disjunctions_to_add):
        for i in range(len(disjunctions)):
            for literal in literals:
                #if disjunctions[i] is not literal:
                disjunctions.append(disjunctions[i]+'|'+literal)

    conjunctive_normal_forms = []
    for d in disjunctions:
        conjunctive_normal_forms.append('('+str(d)+')')

    for _ in range(number_of_conjunctions_to_add):
        for i in range(len(conjunctive_normal_forms)):
            for d in disjunctions:
                #if conjunctive_normal_forms[i] is not d:
                conjunctive_normal_forms.append('('+str(d)+')'+'&'+conjunctive_normal_forms[i])

    statements = list()
    conclusions = list()
    for e in conjunctive_normal_forms:
        statements.append(e)
        conclusions.append(e)

    statement_list = list()
    conclusion_list = list()


    for i in range(len(statements)):
        statement_list.append(["fof(\'"+str(statements[i])+"\',axiom,"+str(statements[i])+").",statements[i]])

    for i in range(len(conclusions)):
        conclusion_list.append(["fof(\'"+str(conclusions[i])+"\',conjecture,"+str(conclusions[i])+").",conclusions[i]])

    theorum_list = list()

    for i in tqdm.tqdm(range(len(statement_list))):
        for j in range(len(conclusion_list)):
            input = statement_list[i][0]+' '+conclusion_list[j][0]
            plaintext = str(statement_list[i][1])+".=>"+str(conclusion_list[j][1])+"."
            theorum_list.append([input,plaintext])

    found_proofs = list()
    unfound_proofs = list()

    for i in tqdm.tqdm(range(len(theorum_list))):
        with io.open(file_path,'w',encoding='utf-8') as f:
            f.write(str(theorum_list[i][0]))

        result = subprocess.run([eprover_path, "--proof-object", str(file_path)], capture_output=True)
        output = result.stdout.decode()

        
        if result.returncode == 0:
            #proof found
            found_proofs.append([str(theorum_list[i][1]),theorum_list[i][0],result]) #[plaintext, e input, e output]

        elif result.returncode == 1:
            #proof not found
            unfound_proofs.append([str(theorum_list[i][1]),theorum_list[i][0],result]) #[plaintext, e input, e output]

        else:
            #something else happened
            print(result)
            raise Exception("Something unexpected occured")

    def format_training_data(found, unfound):
        theorum = []
        non_theorum = []
        for sample in found:
            plaintext = sample[0]
            e_input = sample[1]
            proof = sample[2]
            result = "Found"
            theorum.append([plaintext, e_input, result, proof])

        for sample in unfound:
            plaintext = sample[0]
            e_input = sample[1]
            proof = sample[2]
            result = "Unfound"
            non_theorum.append([plaintext, e_input, result, proof])
        
        return [theorum, non_theorum]

    found,unfound = format_training_data(found_proofs,unfound_proofs)

    #with open('training_data.pickle','wb') as f:
        #pickle.dump(training_data,f)

    with gzip.open('theorum.pickle.gzip','wb') as f:
        pickle.dump(found,f)

    with gzip.open('non_theorum.pickle','wb') as f:
        pickle.dump(unfound,f)

    print("Program Complete")