#!/usr/bin/env node

/**
 * MCP Schema Validation Script
 *
 * Validates JSON Schema files in context/mcp_contracts/ using AJV
 * Used in CI pipeline to ensure schema validity
 */

const fs = require('fs');
const path = require('path');
const Ajv = require('ajv');
const addFormats = require('ajv-formats');

const ajv = new Ajv({ allErrors: true, verbose: true });
addFormats(ajv);

/**
 * Validate a JSON schema file
 * @param {string} filePath - Path to the JSON schema file
 * @returns {boolean} - True if valid, false otherwise
 */
function validateSchemaFile(filePath) {
    try {
        console.log(`Validating: ${filePath}`);

        // Read and parse JSON
        const schemaContent = fs.readFileSync(filePath, 'utf8');
        const schema = JSON.parse(schemaContent);

        // Validate against JSON Schema meta-schema
        const valid = ajv.validateSchema(schema);

        if (valid) {
            console.log(`✅ ${path.basename(filePath)}: Valid JSON Schema`);

            // Additional checks for MCP contract structure
            if (schema.definitions) {
                const requiredTools = ['store_context', 'retrieve_context', 'get_agent_state'];
                const definedTools = Object.keys(schema.definitions);
                const missingTools = requiredTools.filter(tool => !definedTools.includes(tool));

                if (missingTools.length === 0) {
                    console.log(`✅ ${path.basename(filePath)}: All required MCP tools defined`);
                } else {
                    console.error(`❌ ${path.basename(filePath)}: Missing tools: ${missingTools.join(', ')}`);
                    return false;
                }
            }

            // Check examples structure
            if (schema.examples && Array.isArray(schema.examples)) {
                const exampleTools = schema.examples.map(ex => ex.tool);
                const requiredTools = ['store_context', 'retrieve_context', 'get_agent_state'];
                const missingExamples = requiredTools.filter(tool => !exampleTools.includes(tool));

                if (missingExamples.length === 0) {
                    console.log(`✅ ${path.basename(filePath)}: All required tools have examples`);
                } else {
                    console.error(`❌ ${path.basename(filePath)}: Missing examples for: ${missingExamples.join(', ')}`);
                    return false;
                }
            }

            return true;
        } else {
            console.error(`❌ ${path.basename(filePath)}: Invalid JSON Schema`);
            if (ajv.errors) {
                ajv.errors.forEach(error => {
                    console.error(`   Error: ${error.instancePath} ${error.message}`);
                    if (error.data !== undefined) {
                        console.error(`   Data: ${JSON.stringify(error.data, null, 2)}`);
                    }
                });
            }
            return false;
        }

    } catch (error) {
        console.error(`❌ ${path.basename(filePath)}: ${error.message}`);
        return false;
    }
}

/**
 * Main validation function
 */
function main() {
    const contractsDir = path.join(__dirname, '..', 'context', 'mcp_contracts');

    console.log('🔍 MCP Schema Validation');
    console.log('========================');

    if (!fs.existsSync(contractsDir)) {
        console.error(`❌ Directory not found: ${contractsDir}`);
        process.exit(1);
    }

    const files = fs.readdirSync(contractsDir)
        .filter(file => file.endsWith('.json'))
        .map(file => path.join(contractsDir, file));

    if (files.length === 0) {
        console.log('⚠️  No JSON schema files found in context/mcp_contracts/');
        process.exit(0);
    }

    let allValid = true;

    files.forEach(file => {
        const isValid = validateSchemaFile(file);
        if (!isValid) {
            allValid = false;
        }
        console.log(''); // Empty line for readability
    });

    if (allValid) {
        console.log('🎉 All MCP schemas are valid!');
        process.exit(0);
    } else {
        console.error('💥 Some MCP schemas failed validation');
        process.exit(1);
    }
}

// Run if called directly
if (require.main === module) {
    main();
}

module.exports = { validateSchemaFile };
